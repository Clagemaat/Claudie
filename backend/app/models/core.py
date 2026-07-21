import uuid

from sqlalchemy import Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPKMixin
from app.models.enums import ProjectStatus


class Customer(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "customers"

    name: Mapped[str] = mapped_column(String(255))


class Retailer(Base, UUIDPKMixin, TimestampMixin):
    """A retail chain/store a design is being made for - distinct from
    Customer, since one customer (e.g. an agency) can place designs for
    several different retailers."""

    __tablename__ = "retailers"

    customer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("customers.id"))
    name: Mapped[str] = mapped_column(String(255))


class ProductType(Base, UUIDPKMixin):
    __tablename__ = "product_types"

    name: Mapped[str] = mapped_column(String(255), unique=True)


class Location(Base, UUIDPKMixin):
    __tablename__ = "locations"

    name: Mapped[str] = mapped_column(String(255), unique=True)


class Project(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "projects"

    name: Mapped[str] = mapped_column(String(255))
    customer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("customers.id"))
    created_by_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    status: Mapped[ProjectStatus] = mapped_column(
        Enum(ProjectStatus, name="project_status"), default=ProjectStatus.OPEN
    )
