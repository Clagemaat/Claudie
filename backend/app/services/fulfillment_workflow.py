import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.core import Project
from app.models.costing import PricingRequest, QuoteLine
from app.models.design import TemplateVersion
from app.models.enums import (
    ItemCreationStatus,
    OrderStatus,
    PricingRequestSourceType,
    QuoteLineStatus,
    Role,
)
from app.models.fulfillment import ItemCreationRequest, Order, OrderLine
from app.schemas.fulfillment import CompleteItemCreationRequest, OrderCreate
from app.services.ops import audit, complete_tasks, create_task, now, user_has_role

ENTITY_TYPE_ORDER = "order"
ENTITY_TYPE_ITEM = "item_creation_request"


class WorkflowError(Exception):
    """A business-rule violation: wrong status, wrong actor, missing input."""


def create_order(db: Session, project: Project, payload: OrderCreate) -> Order:
    if not payload.lines:
        raise WorkflowError("at least one line is required")

    order = Order(
        project_id=project.id,
        customer_id=project.customer_id,
        created_by_id=payload.created_by_id,
        status=OrderStatus.PENDING_ITEM_CREATION,
    )
    db.add(order)
    db.flush()

    for line_in in payload.lines:
        quote_line = db.get(QuoteLine, line_in.quote_line_id)
        if quote_line is None:
            raise WorkflowError(f"quote line {line_in.quote_line_id} not found")
        if quote_line.status != QuoteLineStatus.PRICED:
            raise WorkflowError("can only order quote lines that have already been priced")

        pricing_request = db.get(PricingRequest, quote_line.pricing_request_id)
        if (
            pricing_request.source_type != PricingRequestSourceType.TEMPLATE
            or pricing_request.template_version_id is None
        ):
            raise WorkflowError(
                "only quotes based on a design template can be ordered - "
                "questions-only quotes have no item to create"
            )

        template_version = db.get(TemplateVersion, pricing_request.template_version_id)
        design_request_id = template_version.design_request_id

        # Color+size determines a distinct ERP item; production/delivery
        # location doesn't - so reuse an existing (pending or already
        # fulfilled) ItemCreationRequest for the same template+color+size
        # instead of creating a duplicate one.
        item_request = db.scalar(
            select(ItemCreationRequest).where(
                ItemCreationRequest.design_request_id == design_request_id,
                ItemCreationRequest.color == quote_line.color,
                ItemCreationRequest.size == quote_line.size,
            )
        )
        if item_request is None:
            item_request = ItemCreationRequest(
                design_request_id=design_request_id,
                color=quote_line.color,
                size=quote_line.size,
                status=ItemCreationStatus.PENDING,
            )
            db.add(item_request)
            db.flush()
            create_task(db, ENTITY_TYPE_ITEM, item_request.id, "create_item", assigned_to_role=Role.ITEM_CREATOR)

        db.add(OrderLine(
            order_id=order.id,
            quote_line_id=quote_line.id,
            quantity_ordered=line_in.quantity_ordered,
            item_creation_request_id=item_request.id,
        ))

    db.flush()
    _recompute_order_status(db, order)
    audit(
        db, ENTITY_TYPE_ORDER, order.id, "order_created", payload.created_by_id,
        after={"status": order.status.value},
    )

    db.commit()
    db.refresh(order)
    return order


def _recompute_order_status(db: Session, order: Order) -> None:
    lines = db.scalars(select(OrderLine).where(OrderLine.order_id == order.id)).all()
    item_ids = {line.item_creation_request_id for line in lines}
    items = db.scalars(
        select(ItemCreationRequest).where(ItemCreationRequest.id.in_(item_ids))
    ).all() if item_ids else []

    if items and all(item.status == ItemCreationStatus.DONE for item in items):
        order.status = OrderStatus.READY
    else:
        order.status = OrderStatus.PENDING_ITEM_CREATION


def complete_item_creation(
    db: Session, item_request: ItemCreationRequest, payload: CompleteItemCreationRequest
) -> ItemCreationRequest:
    if item_request.status == ItemCreationStatus.DONE:
        raise WorkflowError("this item has already been created")
    if not user_has_role(db, payload.actor_id, Role.ITEM_CREATOR):
        raise WorkflowError("actor must be an Item Creator")

    item_request.assigned_item_creator_id = payload.actor_id
    item_request.erp_item_number = payload.erp_item_number
    item_request.status = ItemCreationStatus.DONE
    item_request.completed_at = now()

    complete_tasks(db, ENTITY_TYPE_ITEM, item_request.id, "create_item")
    audit(
        db, ENTITY_TYPE_ITEM, item_request.id, "item_created", payload.actor_id,
        after={"erp_item_number": payload.erp_item_number},
    )

    # This item may be shared by multiple orders/order lines (dedup by
    # color+size) - recompute every affected order's status, so sales sees
    # "ready" the moment the last outstanding item on their order is done.
    order_ids = db.scalars(
        select(OrderLine.order_id).where(OrderLine.item_creation_request_id == item_request.id)
    ).all()
    for order_id in set(order_ids):
        order = db.get(Order, order_id)
        _recompute_order_status(db, order)

    db.commit()
    db.refresh(item_request)
    return item_request
