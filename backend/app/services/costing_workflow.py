import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.core import Project
from app.models.costing import Factory, FactoryQuoteOption, PricingRequest, QuoteLine
from app.models.design import DesignRequest, TemplateVersion
from app.models.enums import (
    PricingRequestSourceType,
    PricingRequestStatus,
    QuoteLineStatus,
    RequestCategory,
    Role,
    TemplateVersionStatus,
)
from app.models.fulfillment import ItemCreationRequest, Order, OrderLine
from app.models.reference_data import DutyRate, ExchangeRate, FreightRate, HandlingCost
from app.schemas.costing import (
    AddLineRequest,
    ClaimRequest,
    FactoryQuoteOptionCreate,
    OverrideLineRequest,
    PriceLineRequest,
    PricingRequestCreate,
)
from app.services.ops import audit, complete_tasks, create_task, user_has_role

ENTITY_TYPE = "pricing_request"


class WorkflowError(Exception):
    """A business-rule violation: wrong status, wrong actor, missing input."""


def _resolve_product_type_id(db: Session, pr: PricingRequest) -> uuid.UUID | None:
    if pr.product_type_id is not None:
        return pr.product_type_id
    if pr.template_version_id is not None:
        version = db.get(TemplateVersion, pr.template_version_id)
        if version is not None:
            design_request = db.get(DesignRequest, version.design_request_id)
            if design_request is not None:
                return design_request.product_type_id
    return None


def create_pricing_request(
    db: Session, project_id: uuid.UUID, payload: PricingRequestCreate
) -> PricingRequest:
    if payload.source_type == PricingRequestSourceType.TEMPLATE:
        if payload.template_version_id is None:
            raise WorkflowError("template_version_id is required when source_type is 'template'")
        version = db.get(TemplateVersion, payload.template_version_id)
        if version is None:
            raise WorkflowError("template_version not found")
        if version.status != TemplateVersionStatus.FINAL_READY:
            raise WorkflowError("the template must be final-ready before you can proceed to quote")
    elif payload.product_type_id is None:
        raise WorkflowError("product_type_id is required when source_type is 'questions'")

    if not payload.lines:
        raise WorkflowError("at least one variation/line is required")

    pr = PricingRequest(
        project_id=project_id,
        category=RequestCategory.PRICING,
        created_by_id=payload.created_by_id,
        source_type=payload.source_type,
        template_version_id=payload.template_version_id,
        product_type_id=payload.product_type_id,
        questions=payload.questions,
        requested_delivery_date=payload.requested_delivery_date,
        requested_quote_validity_until=payload.requested_quote_validity_until,
        status=PricingRequestStatus.OPEN,
    )
    db.add(pr)
    db.flush()

    for line_in in payload.lines:
        db.add(QuoteLine(
            pricing_request_id=pr.id, status=QuoteLineStatus.REQUESTED, **line_in.model_dump()
        ))

    create_task(db, ENTITY_TYPE, pr.id, "claim", assigned_to_role=Role.COSTING)
    audit(db, ENTITY_TYPE, pr.id, "submitted", payload.created_by_id, after={"status": pr.status.value})

    db.commit()
    db.refresh(pr)
    return pr


def claim(db: Session, pr: PricingRequest, payload: ClaimRequest) -> PricingRequest:
    if pr.assigned_costing_user_id is not None:
        raise WorkflowError("this pricing request has already been claimed")
    if not user_has_role(db, payload.actor_id, Role.COSTING):
        raise WorkflowError("actor must be a Costing user")

    pr.assigned_costing_user_id = payload.actor_id
    pr.status = PricingRequestStatus.IN_PROGRESS

    complete_tasks(db, ENTITY_TYPE, pr.id, "claim")
    create_task(db, ENTITY_TYPE, pr.id, "pricing", assigned_to_user_id=payload.actor_id)
    audit(
        db, ENTITY_TYPE, pr.id, "claimed", payload.actor_id,
        after={"assigned_costing_user_id": str(payload.actor_id)},
    )

    db.commit()
    db.refresh(pr)
    return pr


def add_line(db: Session, pr: PricingRequest, payload: AddLineRequest) -> QuoteLine:
    line = QuoteLine(
        pricing_request_id=pr.id,
        color=payload.color,
        size=payload.size,
        quantity=payload.quantity,
        production_location_id=payload.production_location_id,
        delivery_location_id=payload.delivery_location_id,
        status=QuoteLineStatus.REQUESTED,
    )
    db.add(line)

    # A completed request reopens; new lines on an open/in-progress request
    # don't need a status change - existing priced lines are untouched.
    if pr.status == PricingRequestStatus.COMPLETE:
        pr.status = PricingRequestStatus.IN_PROGRESS

    if pr.assigned_costing_user_id is not None:
        create_task(db, ENTITY_TYPE, pr.id, "pricing", assigned_to_user_id=pr.assigned_costing_user_id)
    else:
        create_task(db, ENTITY_TYPE, pr.id, "claim", assigned_to_role=Role.COSTING)

    audit(db, ENTITY_TYPE, pr.id, "line_added", payload.actor_id, after={"status": pr.status.value})

    db.commit()
    db.refresh(line)
    return line


def _compute_volume_cbm(width_cm: float, length_cm: float, height_cm: float, qty: int) -> float:
    return (float(width_cm) * float(length_cm) * float(height_cm) / 1_000_000) * int(qty)


def _compute_landed_cost(
    db: Session,
    hs_code: str,
    product_type_id: uuid.UUID,
    production_location_id: uuid.UUID,
    delivery_location_id: uuid.UUID,
    purchase_price: float,
    purchase_currency: str,
    volume_cbm: float,
) -> dict:
    """purchase price (converted to EUR) + freight (volume x cost/cbm) +
    duty ((material + freight) x duty rate) + handling cost."""
    fx_rate = db.scalar(
        select(ExchangeRate)
        .where(ExchangeRate.currency == purchase_currency)
        .order_by(ExchangeRate.effective_date.desc())
    )
    if fx_rate is None:
        raise WorkflowError(f"no exchange rate configured for currency {purchase_currency}")

    freight_rate = db.scalar(
        select(FreightRate).where(
            FreightRate.production_location_id == production_location_id,
            FreightRate.delivery_location_id == delivery_location_id,
        )
    )
    if freight_rate is None:
        raise WorkflowError("no freight rate configured for this production/delivery lane")

    duty_rate = db.scalar(
        select(DutyRate).where(
            DutyRate.hs_code == hs_code,
            DutyRate.destination_location_id == delivery_location_id,
        )
    )
    if duty_rate is None:
        raise WorkflowError(f"no duty rate configured for HS code {hs_code} to this destination")

    handling = db.scalar(
        select(HandlingCost).where(HandlingCost.product_type_id == product_type_id)
    )
    if handling is None:
        raise WorkflowError("no handling cost configured for this product type")

    purchase_price_eur = float(purchase_price) * float(fx_rate.rate_to_eur)
    freight_cost = float(volume_cbm) * float(freight_rate.cost_per_cbm)
    duty_cost = (purchase_price_eur + freight_cost) * float(duty_rate.rate_pct) / 100
    handling_cost = float(handling.cost)

    return {
        "fx_rate_to_eur": fx_rate.rate_to_eur,
        "freight_cost": freight_cost,
        "duty_cost": duty_cost,
        "handling_cost": handling_cost,
        "landed_cost": purchase_price_eur + freight_cost + duty_cost + handling_cost,
    }


def _apply_costs_to_line(line: QuoteLine, costs: dict, margin_pct: float) -> None:
    line.fx_rate_to_eur = costs["fx_rate_to_eur"]
    line.freight_cost = costs["freight_cost"]
    line.duty_cost = costs["duty_cost"]
    line.handling_cost = costs["handling_cost"]
    line.landed_cost = costs["landed_cost"]
    line.margin_pct = margin_pct
    line.sell_price = costs["landed_cost"] * (1 + margin_pct / 100)
    line.status = QuoteLineStatus.PRICED


def _recompute_pricing_request_status(db: Session, pr: PricingRequest) -> None:
    lines = db.scalars(
        select(QuoteLine).where(QuoteLine.pricing_request_id == pr.id)
    ).all()
    if lines and all(line.status == QuoteLineStatus.PRICED for line in lines):
        if pr.status != PricingRequestStatus.COMPLETE:
            pr.status = PricingRequestStatus.COMPLETE
            complete_tasks(db, ENTITY_TYPE, pr.id, "pricing")
    elif pr.status == PricingRequestStatus.OPEN:
        pr.status = PricingRequestStatus.IN_PROGRESS


def price_line(
    db: Session, pr: PricingRequest, line: QuoteLine, payload: PriceLineRequest
) -> QuoteLine:
    if line.pricing_request_id != pr.id:
        raise WorkflowError("line does not belong to this pricing request")
    if pr.assigned_costing_user_id != payload.actor_id:
        raise WorkflowError("only the costing person assigned to this request can price it")

    product_type_id = _resolve_product_type_id(db, pr)
    if product_type_id is None:
        raise WorkflowError("this pricing request has no product type set - cannot price")
    if db.get(Factory, payload.factory_id) is None:
        raise WorkflowError("factory not found")

    volume_cbm = _compute_volume_cbm(
        payload.box_width_cm, payload.box_length_cm, payload.box_height_cm, payload.box_qty
    )
    costs = _compute_landed_cost(
        db, payload.hs_code, product_type_id, line.production_location_id, line.delivery_location_id,
        payload.purchase_price, payload.purchase_currency, volume_cbm,
    )

    line.factory_id = payload.factory_id
    line.hs_code = payload.hs_code
    line.purchase_price = payload.purchase_price
    line.purchase_currency = payload.purchase_currency
    line.box_width_cm = payload.box_width_cm
    line.box_length_cm = payload.box_length_cm
    line.box_height_cm = payload.box_height_cm
    line.box_qty = payload.box_qty
    line.volume_cbm = volume_cbm
    _apply_costs_to_line(line, costs, payload.margin_pct)

    _recompute_pricing_request_status(db, pr)
    audit(
        db, ENTITY_TYPE, pr.id, "line_priced", payload.actor_id,
        after={"line_id": str(line.id), "sell_price": line.sell_price},
    )

    db.commit()
    db.refresh(line)
    return line


def override_line(
    db: Session, pr: PricingRequest, line: QuoteLine, payload: OverrideLineRequest
) -> QuoteLine:
    if line.pricing_request_id != pr.id:
        raise WorkflowError("line does not belong to this pricing request")
    if not user_has_role(db, payload.actor_id, Role.SALES_DIRECTOR):
        raise WorkflowError("actor must be a Sales Director")

    factory_id = payload.factory_id or line.factory_id
    hs_code = payload.hs_code or line.hs_code
    purchase_price = payload.purchase_price if payload.purchase_price is not None else line.purchase_price
    purchase_currency = payload.purchase_currency or line.purchase_currency
    box_width_cm = payload.box_width_cm if payload.box_width_cm is not None else line.box_width_cm
    box_length_cm = payload.box_length_cm if payload.box_length_cm is not None else line.box_length_cm
    box_height_cm = payload.box_height_cm if payload.box_height_cm is not None else line.box_height_cm
    box_qty = payload.box_qty if payload.box_qty is not None else line.box_qty
    margin_pct = payload.margin_pct if payload.margin_pct is not None else line.margin_pct

    if None in (
        factory_id, hs_code, purchase_price, purchase_currency,
        box_width_cm, box_length_cm, box_height_cm, box_qty, margin_pct,
    ):
        raise WorkflowError(
            "line must already be priced, or every field provided, before it can be overridden"
        )

    # Numeric columns loaded from the DB come back as Decimal, which isn't
    # JSON-serializable for the audit log or arithmetic-safe to mix with
    # plain floats - normalize to float as soon as they're resolved.
    purchase_price = float(purchase_price)
    box_width_cm = float(box_width_cm)
    box_length_cm = float(box_length_cm)
    box_height_cm = float(box_height_cm)
    box_qty = int(box_qty)
    margin_pct = float(margin_pct)

    product_type_id = _resolve_product_type_id(db, pr)
    if product_type_id is None:
        raise WorkflowError("this pricing request has no product type set")

    before = {
        "purchase_price": float(line.purchase_price) if line.purchase_price is not None else None,
        "margin_pct": float(line.margin_pct) if line.margin_pct is not None else None,
        "sell_price": float(line.sell_price) if line.sell_price is not None else None,
    }

    volume_cbm = _compute_volume_cbm(box_width_cm, box_length_cm, box_height_cm, box_qty)
    costs = _compute_landed_cost(
        db, hs_code, product_type_id, line.production_location_id, line.delivery_location_id,
        purchase_price, purchase_currency, volume_cbm,
    )

    line.factory_id = factory_id
    line.hs_code = hs_code
    line.purchase_price = purchase_price
    line.purchase_currency = purchase_currency
    line.box_width_cm = box_width_cm
    line.box_length_cm = box_length_cm
    line.box_height_cm = box_height_cm
    line.box_qty = box_qty
    line.volume_cbm = volume_cbm
    _apply_costs_to_line(line, costs, margin_pct)

    _recompute_pricing_request_status(db, pr)
    audit(
        db, ENTITY_TYPE, pr.id, "line_overridden", payload.actor_id,
        before=before,
        after={
            "purchase_price": line.purchase_price,
            "margin_pct": line.margin_pct,
            "sell_price": line.sell_price,
        },
        is_override=True,
    )

    db.commit()
    db.refresh(line)
    return line


def add_quote_option(
    db: Session, line: QuoteLine, payload: FactoryQuoteOptionCreate
) -> FactoryQuoteOption:
    """Optional bookkeeping - logging a competing factory offer never
    blocks or is required before pricing a line via price_line()."""
    if db.get(Factory, payload.factory_id) is None:
        raise WorkflowError("factory not found")

    option = FactoryQuoteOption(
        quote_line_id=line.id,
        factory_id=payload.factory_id,
        quoted_price=payload.quoted_price,
        currency=payload.currency,
        notes=payload.notes,
    )
    db.add(option)
    db.commit()
    db.refresh(option)
    return option


def select_quote_option(
    db: Session, line: QuoteLine, option: FactoryQuoteOption
) -> FactoryQuoteOption:
    if option.quote_line_id != line.id:
        raise WorkflowError("quote option does not belong to this line")

    others = db.scalars(
        select(FactoryQuoteOption).where(
            FactoryQuoteOption.quote_line_id == line.id,
            FactoryQuoteOption.id != option.id,
        )
    ).all()
    for other in others:
        other.is_selected = False
    option.is_selected = True

    db.commit()
    db.refresh(option)
    return option


def estimate_option_landed_cost(
    db: Session, pr: PricingRequest, line: QuoteLine, quoted_price: float, currency: str
) -> float | None:
    """Reuses the line's already-set hs_code/volume (from when it was
    priced) to estimate what landed cost this competing offer would produce
    - returns None if the line hasn't been priced yet, since box
    dimensions/HS code aren't known until then."""
    if line.hs_code is None or line.volume_cbm is None:
        return None
    product_type_id = _resolve_product_type_id(db, pr)
    if product_type_id is None:
        return None
    try:
        costs = _compute_landed_cost(
            db, line.hs_code, product_type_id, line.production_location_id,
            line.delivery_location_id, quoted_price, currency, float(line.volume_cbm),
        )
    except WorkflowError:
        return None
    return costs["landed_cost"]


def get_margin_recommendation(db: Session, pr: PricingRequest) -> tuple[float | None, int]:
    """Average margin from other PRICED lines for the same customer and
    product type, but only where the business was actually won (an
    Order line resolved to an ItemCreationRequest with a real ERP item
    number)."""
    product_type_id = _resolve_product_type_id(db, pr)
    project = db.get(Project, pr.project_id)
    if product_type_id is None or project is None:
        return None, 0

    won_project_ids = (
        select(Order.project_id)
        .join(OrderLine, OrderLine.order_id == Order.id)
        .join(ItemCreationRequest, ItemCreationRequest.id == OrderLine.item_creation_request_id)
        .where(ItemCreationRequest.erp_item_number.is_not(None))
    )

    effective_product_type = func.coalesce(PricingRequest.product_type_id, DesignRequest.product_type_id)

    rows = db.scalars(
        select(QuoteLine.margin_pct)
        .join(PricingRequest, PricingRequest.id == QuoteLine.pricing_request_id)
        .join(Project, Project.id == PricingRequest.project_id)
        .outerjoin(TemplateVersion, TemplateVersion.id == PricingRequest.template_version_id)
        .outerjoin(DesignRequest, DesignRequest.id == TemplateVersion.design_request_id)
        .where(
            QuoteLine.status == QuoteLineStatus.PRICED,
            Project.customer_id == project.customer_id,
            PricingRequest.project_id.in_(won_project_ids),
            effective_product_type == product_type_id,
        )
    ).all()

    if not rows:
        return None, 0
    values = [float(v) for v in rows]
    return sum(values) / len(values), len(values)
