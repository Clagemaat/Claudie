import uuid
from datetime import date

from pydantic import BaseModel, ConfigDict


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
