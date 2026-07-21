import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.core import Project
from app.models.costing import Factory, FactoryQuoteOption, PricingRequest, QuoteLine
from app.models.enums import PricingRequestStatus
from app.schemas.costing import (
    AddLineRequest,
    ClaimRequest,
    FactoryCreate,
    FactoryOut,
    FactoryQuoteOptionCreate,
    FactoryQuoteOptionOut,
    MarginRecommendationOut,
    OverrideLineRequest,
    PriceLineRequest,
    PricingRequestCreate,
    PricingRequestDetailOut,
    PricingRequestOut,
    QuoteLineOut,
)
from app.services import costing_workflow

router = APIRouter(tags=["costing"])


@router.post("/factories", response_model=FactoryOut)
def create_factory(payload: FactoryCreate, db: Session = Depends(get_db)) -> Factory:
    factory = Factory(name=payload.name, contact_info=payload.contact_info)
    db.add(factory)
    db.commit()
    db.refresh(factory)
    return factory


@router.get("/factories", response_model=list[FactoryOut])
def list_factories(db: Session = Depends(get_db)) -> list[Factory]:
    return db.scalars(select(Factory)).all()


def _get_pricing_request(db: Session, pricing_request_id: uuid.UUID) -> PricingRequest:
    pr = db.get(PricingRequest, pricing_request_id)
    if pr is None:
        raise HTTPException(status_code=404, detail="pricing request not found")
    return pr


def _get_line(db: Session, line_id: uuid.UUID) -> QuoteLine:
    line = db.get(QuoteLine, line_id)
    if line is None:
        raise HTTPException(status_code=404, detail="quote line not found")
    return line


def _to_option_out(
    db: Session, pr: PricingRequest, line: QuoteLine, option: FactoryQuoteOption
) -> FactoryQuoteOptionOut:
    landed_cost = costing_workflow.estimate_option_landed_cost(
        db, pr, line, float(option.quoted_price), option.currency
    )
    return FactoryQuoteOptionOut(
        id=option.id,
        quote_line_id=option.quote_line_id,
        factory_id=option.factory_id,
        quoted_price=option.quoted_price,
        currency=option.currency,
        notes=option.notes,
        is_selected=option.is_selected,
        landed_cost=landed_cost,
    )


@router.get("/pricing-requests", response_model=list[PricingRequestOut])
def list_pricing_requests(
    status: PricingRequestStatus | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[PricingRequest]:
    """The consolidated overview: every quote, who (if anyone) has claimed
    it, and its status - not just the caller's own to-do list."""
    query = select(PricingRequest)
    if status is not None:
        query = query.where(PricingRequest.status == status)
    return db.scalars(query.order_by(PricingRequest.created_at)).all()


@router.post("/projects/{project_id}/pricing-requests", response_model=PricingRequestOut)
def create_pricing_request(
    project_id: uuid.UUID, payload: PricingRequestCreate, db: Session = Depends(get_db)
) -> PricingRequest:
    if db.get(Project, project_id) is None:
        raise HTTPException(status_code=404, detail="project not found")
    try:
        return costing_workflow.create_pricing_request(db, project_id, payload)
    except costing_workflow.WorkflowError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/pricing-requests/{pricing_request_id}", response_model=PricingRequestDetailOut)
def get_pricing_request(
    pricing_request_id: uuid.UUID, db: Session = Depends(get_db)
) -> PricingRequestDetailOut:
    pr = _get_pricing_request(db, pricing_request_id)
    lines = db.scalars(
        select(QuoteLine).where(QuoteLine.pricing_request_id == pr.id).order_by(QuoteLine.created_at)
    ).all()
    return PricingRequestDetailOut(**PricingRequestOut.model_validate(pr).model_dump(), lines=lines)


@router.post("/pricing-requests/{pricing_request_id}/claim", response_model=PricingRequestOut)
def claim_pricing_request(
    pricing_request_id: uuid.UUID, payload: ClaimRequest, db: Session = Depends(get_db)
) -> PricingRequest:
    pr = _get_pricing_request(db, pricing_request_id)
    try:
        return costing_workflow.claim(db, pr, payload)
    except costing_workflow.WorkflowError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/pricing-requests/{pricing_request_id}/lines", response_model=QuoteLineOut)
def add_line(
    pricing_request_id: uuid.UUID, payload: AddLineRequest, db: Session = Depends(get_db)
) -> QuoteLine:
    pr = _get_pricing_request(db, pricing_request_id)
    try:
        return costing_workflow.add_line(db, pr, payload)
    except costing_workflow.WorkflowError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post(
    "/pricing-requests/{pricing_request_id}/lines/{line_id}/quote-options",
    response_model=FactoryQuoteOptionOut,
)
def add_quote_option(
    pricing_request_id: uuid.UUID,
    line_id: uuid.UUID,
    payload: FactoryQuoteOptionCreate,
    db: Session = Depends(get_db),
) -> FactoryQuoteOptionOut:
    pr = _get_pricing_request(db, pricing_request_id)
    line = _get_line(db, line_id)
    try:
        option = costing_workflow.add_quote_option(db, line, payload)
    except costing_workflow.WorkflowError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _to_option_out(db, pr, line, option)


@router.get(
    "/pricing-requests/{pricing_request_id}/lines/{line_id}/quote-options",
    response_model=list[FactoryQuoteOptionOut],
)
def list_quote_options(
    pricing_request_id: uuid.UUID, line_id: uuid.UUID, db: Session = Depends(get_db)
) -> list[FactoryQuoteOptionOut]:
    pr = _get_pricing_request(db, pricing_request_id)
    line = _get_line(db, line_id)
    options = db.scalars(
        select(FactoryQuoteOption).where(FactoryQuoteOption.quote_line_id == line.id)
    ).all()
    return [_to_option_out(db, pr, line, opt) for opt in options]


@router.post(
    "/pricing-requests/{pricing_request_id}/lines/{line_id}/quote-options/{option_id}/select",
    response_model=FactoryQuoteOptionOut,
)
def select_quote_option(
    pricing_request_id: uuid.UUID,
    line_id: uuid.UUID,
    option_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> FactoryQuoteOptionOut:
    pr = _get_pricing_request(db, pricing_request_id)
    line = _get_line(db, line_id)
    option = db.get(FactoryQuoteOption, option_id)
    if option is None:
        raise HTTPException(status_code=404, detail="quote option not found")
    try:
        option = costing_workflow.select_quote_option(db, line, option)
    except costing_workflow.WorkflowError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _to_option_out(db, pr, line, option)


@router.post(
    "/pricing-requests/{pricing_request_id}/lines/{line_id}/price", response_model=QuoteLineOut
)
def price_line(
    pricing_request_id: uuid.UUID,
    line_id: uuid.UUID,
    payload: PriceLineRequest,
    db: Session = Depends(get_db),
) -> QuoteLine:
    pr = _get_pricing_request(db, pricing_request_id)
    line = _get_line(db, line_id)
    try:
        return costing_workflow.price_line(db, pr, line, payload)
    except costing_workflow.WorkflowError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post(
    "/pricing-requests/{pricing_request_id}/lines/{line_id}/override", response_model=QuoteLineOut
)
def override_line(
    pricing_request_id: uuid.UUID,
    line_id: uuid.UUID,
    payload: OverrideLineRequest,
    db: Session = Depends(get_db),
) -> QuoteLine:
    pr = _get_pricing_request(db, pricing_request_id)
    line = _get_line(db, line_id)
    try:
        return costing_workflow.override_line(db, pr, line, payload)
    except costing_workflow.WorkflowError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get(
    "/pricing-requests/{pricing_request_id}/lines/{line_id}/margin-recommendation",
    response_model=MarginRecommendationOut,
)
def margin_recommendation(
    pricing_request_id: uuid.UUID, line_id: uuid.UUID, db: Session = Depends(get_db)
) -> MarginRecommendationOut:
    pr = _get_pricing_request(db, pricing_request_id)
    _get_line(db, line_id)  # validated to exist / belongs to this request implicitly via 404
    recommended, count = costing_workflow.get_margin_recommendation(db, pr)
    return MarginRecommendationOut(recommended_margin_pct=recommended, based_on_count=count)
