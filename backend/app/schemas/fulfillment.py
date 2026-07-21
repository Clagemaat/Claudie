import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ItemCreationStatus, OrderStatus


class OrderLineCreate(BaseModel):
    quote_line_id: uuid.UUID
    quantity_ordered: int = Field(ge=1)


class OrderCreate(BaseModel):
    created_by_id: uuid.UUID
    lines: list[OrderLineCreate]


class OrderLineOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    order_id: uuid.UUID
    quote_line_id: uuid.UUID
    quantity_ordered: int
    item_creation_request_id: uuid.UUID | None


class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    customer_id: uuid.UUID
    created_by_id: uuid.UUID
    status: OrderStatus
    created_at: datetime
    updated_at: datetime


class OrderDetailOut(OrderOut):
    lines: list[OrderLineOut] = []


class ItemCreationRequestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    design_request_id: uuid.UUID
    color: str
    size: str
    status: ItemCreationStatus
    assigned_item_creator_id: uuid.UUID | None
    erp_item_number: str | None
    created_at: datetime
    completed_at: datetime | None


class CompleteItemCreationRequest(BaseModel):
    actor_id: uuid.UUID
    erp_item_number: str
