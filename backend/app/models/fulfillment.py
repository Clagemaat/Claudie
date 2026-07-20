import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPKMixin
from app.models.enums import ItemCreationStatus, OrderStatus


class Order(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "orders"

    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id"))
    customer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("customers.id"))
    created_by_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus, name="order_status"),
        default=OrderStatus.PENDING_ITEM_CREATION,
    )

    lines: Mapped[list["OrderLine"]] = relationship(back_populates="order")


class OrderLine(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "order_lines"

    order_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("orders.id"))
    quote_line_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("quote_lines.id"))
    quantity_ordered: Mapped[int]
    # Set once resolved against an ItemCreationRequest - either a newly
    # created one, or an existing one reused for the same (template, color,
    # size) combination.
    item_creation_request_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("item_creation_requests.id"), nullable=True
    )

    order: Mapped["Order"] = relationship(back_populates="lines")


class ItemCreationRequest(Base, UUIDPKMixin, TimestampMixin):
    """One per unique (design_request, color, size) combination.

    Production/delivery location do NOT create a new item - only color and
    size do, so order lines that share those two dimensions are expected to
    resolve to the same ItemCreationRequest instead of creating a new one.
    """

    __tablename__ = "item_creation_requests"

    design_request_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("design_requests.id")
    )
    color: Mapped[str] = mapped_column(String(100))
    size: Mapped[str] = mapped_column(String(100))
    status: Mapped[ItemCreationStatus] = mapped_column(
        Enum(ItemCreationStatus, name="item_creation_status"),
        default=ItemCreationStatus.PENDING,
    )
    assigned_item_creator_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    # Filled in by the item creator once they've manually created the item
    # in the ERP; later replaced/populated by a direct ERP API call.
    erp_item_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
