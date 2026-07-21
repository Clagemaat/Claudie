import uuid
from datetime import date, timedelta

from pydantic import BaseModel, ConfigDict

from app.models.enums import Role


class LocationCreate(BaseModel):
    name: str


class LocationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str


class ProductTypeCreate(BaseModel):
    name: str


class ProductTypeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str


class ExchangeRateCreate(BaseModel):
    currency: str
    rate_to_eur: float
    effective_date: date


class ExchangeRateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    currency: str
    rate_to_eur: float
    effective_date: date


class FreightRateCreate(BaseModel):
    production_location_id: uuid.UUID
    delivery_location_id: uuid.UUID
    cost_per_cbm: float


class FreightRateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    production_location_id: uuid.UUID
    delivery_location_id: uuid.UUID
    cost_per_cbm: float


class DutyRateCreate(BaseModel):
    hs_code: str
    destination_location_id: uuid.UUID
    rate_pct: float


class DutyRateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    hs_code: str
    destination_location_id: uuid.UUID
    rate_pct: float


class HandlingCostCreate(BaseModel):
    product_type_id: uuid.UUID
    cost: float


class HandlingCostOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    product_type_id: uuid.UUID
    cost: float


class SLADefinitionCreate(BaseModel):
    entity_type: str
    step_name: str
    duration: timedelta
    reminder_frequency: timedelta


class SLADefinitionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    entity_type: str
    step_name: str
    duration: timedelta
    reminder_frequency: timedelta


class EscalationRuleCreate(BaseModel):
    entity_type: str
    step_name: str
    threshold_after_due: timedelta
    escalate_to_role: Role | None = None
    escalate_to_user_id: uuid.UUID | None = None
    notify_message_template: str


class EscalationRuleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    entity_type: str
    step_name: str
    threshold_after_due: timedelta
    escalate_to_role: Role | None
    escalate_to_user_id: uuid.UUID | None
    notify_message_template: str
