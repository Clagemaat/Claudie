import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.core import Project
from app.models.fulfillment import ItemCreationRequest, Order, OrderLine
from app.schemas.fulfillment import (
    CompleteItemCreationRequest,
    ItemCreationRequestOut,
    OrderCreate,
    OrderDetailOut,
    OrderOut,
)
from app.services import fulfillment_workflow

router = APIRouter(tags=["fulfillment"])


@router.post("/projects/{project_id}/orders", response_model=OrderOut)
def create_order(
    project_id: uuid.UUID, payload: OrderCreate, db: Session = Depends(get_db)
) -> Order:
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="project not found")
    try:
        return fulfillment_workflow.create_order(db, project, payload)
    except fulfillment_workflow.WorkflowError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/orders/{order_id}", response_model=OrderDetailOut)
def get_order(order_id: uuid.UUID, db: Session = Depends(get_db)) -> OrderDetailOut:
    order = db.get(Order, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="order not found")
    lines = db.scalars(
        select(OrderLine).where(OrderLine.order_id == order.id).order_by(OrderLine.created_at)
    ).all()
    return OrderDetailOut(**OrderOut.model_validate(order).model_dump(), lines=lines)


@router.get("/item-creation-requests/{item_id}", response_model=ItemCreationRequestOut)
def get_item_creation_request(
    item_id: uuid.UUID, db: Session = Depends(get_db)
) -> ItemCreationRequest:
    item = db.get(ItemCreationRequest, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="item creation request not found")
    return item


@router.post(
    "/item-creation-requests/{item_id}/complete", response_model=ItemCreationRequestOut
)
def complete_item_creation_request(
    item_id: uuid.UUID, payload: CompleteItemCreationRequest, db: Session = Depends(get_db)
) -> ItemCreationRequest:
    item = db.get(ItemCreationRequest, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="item creation request not found")
    try:
        return fulfillment_workflow.complete_item_creation(db, item, payload)
    except fulfillment_workflow.WorkflowError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
