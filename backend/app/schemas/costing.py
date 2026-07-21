import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import PricingRequestSourceType, PricingRequestStatus, QuoteLineStatus


class FactoryCreate(BaseModel):
    name: str
    contact_info: str | None = None


class FactoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    contact_info: str | None


class QuoteLineRequestIn(BaseModel):
    color: str
    size: str
    quantity: int
    production_location_id: uuid.UUID
    delivery_location_id: uuid.UUID


class AddLineRequest(QuoteLineRequestIn):
    actor_id: uuid.UUID


class QuoteLineOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    pricing_request_id: uuid.UUID
    color: str
    size: str
    quantity: int
    production_location_id: uuid.UUID
    delivery_location_id: uuid.UUID
    status: QuoteLineStatus
    factory_id: uuid.UUID | None
    purchase_price: float | None
    purchase_currency: str | None
    fx_rate_to_eur: float | None
    volume_cbm: float | None
    freight_cost: float | None
    duty_cost: float | None
    handling_cost: float | None
    landed_cost: float | None
    margin_pct: float | None
    sell_price: float | None


class PricingRequestCreate(BaseModel):
    created_by_id: uuid.UUID
    source_type: PricingRequestSourceType
    template_version_id: uuid.UUID | None = None
    product_type_id: uuid.UUID | None = None
    questions: dict | None = None
    lines: list[QuoteLineRequestIn]


class PricingRequestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    source_type: PricingRequestSourceType
    template_version_id: uuid.UUID | None
    product_type_id: uuid.UUID | None
    questions: dict | None
    assigned_costing_user_id: uuid.UUID | None
    status: PricingRequestStatus
    created_by_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class PricingRequestDetailOut(PricingRequestOut):
    lines: list[QuoteLineOut] = []


class ClaimRequest(BaseModel):
    actor_id: uuid.UUID


class PriceLineRequest(BaseModel):
    actor_id: uuid.UUID
    factory_id: uuid.UUID
    purchase_price: float
    purchase_currency: str
    volume_cbm: float
    margin_pct: float


class OverrideLineRequest(BaseModel):
    actor_id: uuid.UUID
    factory_id: uuid.UUID | None = None
    purchase_price: float | None = None
    purchase_currency: str | None = None
    volume_cbm: float | None = None
    margin_pct: float | None = None


class MarginRecommendationOut(BaseModel):
    recommended_margin_pct: float | None
    based_on_count: int
