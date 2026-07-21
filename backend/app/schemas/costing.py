import uuid
from datetime import date, datetime

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


class FactoryQuoteOptionCreate(BaseModel):
    factory_id: uuid.UUID
    quoted_price: float
    currency: str
    notes: str | None = None


class FactoryQuoteOptionOut(BaseModel):
    id: uuid.UUID
    quote_line_id: uuid.UUID
    factory_id: uuid.UUID
    quoted_price: float
    currency: str
    notes: str | None
    is_selected: bool
    # Computed on the fly from the line's already-set hs_code/volume (once
    # priced) - null until then, since comparison isn't required upfront.
    landed_cost: float | None


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
    hs_code: str | None
    purchase_price: float | None
    purchase_currency: str | None
    fx_rate_to_eur: float | None
    box_width_cm: float | None
    box_length_cm: float | None
    box_height_cm: float | None
    box_qty: int | None
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
    requested_delivery_date: date | None = None
    requested_quote_validity_until: date | None = None
    lines: list[QuoteLineRequestIn]


class PricingRequestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    source_type: PricingRequestSourceType
    template_version_id: uuid.UUID | None
    product_type_id: uuid.UUID | None
    questions: dict | None
    requested_delivery_date: date | None
    requested_quote_validity_until: date | None
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
    hs_code: str
    purchase_price: float
    purchase_currency: str
    # Box dimensions in centimeters - volume_cbm is derived from these, not
    # entered directly.
    box_width_cm: float
    box_length_cm: float
    box_height_cm: float
    box_qty: int
    margin_pct: float


class OverrideLineRequest(BaseModel):
    actor_id: uuid.UUID
    factory_id: uuid.UUID | None = None
    hs_code: str | None = None
    purchase_price: float | None = None
    purchase_currency: str | None = None
    box_width_cm: float | None = None
    box_length_cm: float | None = None
    box_height_cm: float | None = None
    box_qty: int | None = None
    margin_pct: float | None = None


class MarginRecommendationOut(BaseModel):
    recommended_margin_pct: float | None
    based_on_count: int
