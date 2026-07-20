import uuid

from sqlalchemy import JSON, Boolean, Enum, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPKMixin
from app.models.design import Request
from app.models.enums import (
    PricingRequestSourceType,
    PricingRequestStatus,
    QuoteLineStatus,
    RequestCategory,
)


class PricingRequest(Request):
    __tablename__ = "pricing_requests"

    id: Mapped[uuid.UUID] = mapped_column(ForeignKey("requests.id"), primary_key=True)
    source_type: Mapped[PricingRequestSourceType] = mapped_column(
        Enum(PricingRequestSourceType, name="pricing_request_source_type")
    )
    # Required when source_type=TEMPLATE; the design request's product_type
    # is used when source_type=QUESTIONS has none of its own set explicitly.
    template_version_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("template_versions.id"), nullable=True
    )
    product_type_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("product_types.id"), nullable=True
    )
    questions: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    assigned_costing_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    # Derived from the completion state of its QuoteLines, but persisted for
    # cheap listing/filtering.
    status: Mapped[PricingRequestStatus] = mapped_column(
        Enum(PricingRequestStatus, name="pricing_request_status"),
        default=PricingRequestStatus.OPEN,
    )

    lines: Mapped[list["QuoteLine"]] = relationship(back_populates="pricing_request")

    __mapper_args__ = {
        "polymorphic_identity": RequestCategory.PRICING,
    }


class QuoteLine(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "quote_lines"

    pricing_request_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("pricing_requests.id")
    )
    color: Mapped[str] = mapped_column(String(100))
    size: Mapped[str] = mapped_column(String(100))
    quantity: Mapped[int]
    production_location_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("locations.id")
    )
    delivery_location_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("locations.id")
    )
    status: Mapped[QuoteLineStatus] = mapped_column(
        Enum(QuoteLineStatus, name="quote_line_status"),
        default=QuoteLineStatus.REQUESTED,
    )
    factory_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("factories.id"), nullable=True
    )

    # Costing inputs / calculated landed cost breakdown - populated once priced.
    purchase_price: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    purchase_currency: Mapped[str | None] = mapped_column(String(3), nullable=True)
    fx_rate_to_eur: Mapped[float | None] = mapped_column(Numeric(12, 6), nullable=True)
    volume_cbm: Mapped[float | None] = mapped_column(Numeric(12, 4), nullable=True)
    freight_cost: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    duty_cost: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    handling_cost: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    landed_cost: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    margin_pct: Mapped[float | None] = mapped_column(Numeric(6, 3), nullable=True)
    sell_price: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)

    pricing_request: Mapped["PricingRequest"] = relationship(back_populates="lines")
    quote_options: Mapped[list["FactoryQuoteOption"]] = relationship(
        back_populates="quote_line"
    )


class Factory(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "factories"

    name: Mapped[str] = mapped_column(String(255))
    contact_info: Mapped[str | None] = mapped_column(Text, nullable=True)


class FactoryQuoteOption(Base, UUIDPKMixin, TimestampMixin):
    """A competing offer from one factory for a quote line.

    Optional bookkeeping - costing isn't required to log every offer, just
    the one they select, but can log more for comparison.
    """

    __tablename__ = "factory_quote_options"

    quote_line_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("quote_lines.id"))
    factory_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("factories.id"))
    quoted_price: Mapped[float] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(String(3))
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_selected: Mapped[bool] = mapped_column(Boolean, default=False)

    quote_line: Mapped["QuoteLine"] = relationship(back_populates="quote_options")
