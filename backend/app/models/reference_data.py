import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDPKMixin


class ExchangeRate(Base, UUIDPKMixin):
    __tablename__ = "exchange_rates"

    currency: Mapped[str] = mapped_column(String(3))
    rate_to_eur: Mapped[float] = mapped_column(Numeric(12, 6))
    effective_date: Mapped[date] = mapped_column(Date)


class FreightRate(Base, UUIDPKMixin):
    __tablename__ = "freight_rates"

    production_location_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("locations.id")
    )
    delivery_location_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("locations.id")
    )
    cost_per_cbm: Mapped[float] = mapped_column(Numeric(12, 2))


class DutyRate(Base, UUIDPKMixin):
    __tablename__ = "duty_rates"

    product_type_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("product_types.id"))
    destination_location_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("locations.id")
    )
    rate_pct: Mapped[float] = mapped_column(Numeric(6, 3))


class HandlingCost(Base, UUIDPKMixin):
    __tablename__ = "handling_costs"

    product_type_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("product_types.id"))
    cost: Mapped[float] = mapped_column(Numeric(12, 2))
