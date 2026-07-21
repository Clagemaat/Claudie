import uuid
from datetime import date

from sqlalchemy import ARRAY, Date, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPKMixin
from app.models.enums import (
    DesignRequestStatus,
    DesignRequestSubtype,
    RequestCategory,
    TemplateVersionStatus,
    TemplateVersionTrigger,
)


class Request(Base, UUIDPKMixin, TimestampMixin):
    """Common header shared by every request type (design or pricing).

    Joined-table inheritance: DesignRequest/PricingRequest each add their
    own table keyed on this table's id.
    """

    __tablename__ = "requests"

    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id"))
    category: Mapped[RequestCategory] = mapped_column(
        Enum(RequestCategory, name="request_category")
    )
    created_by_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))

    __mapper_args__ = {
        "polymorphic_on": category,
        "polymorphic_identity": None,
    }


class DesignRequest(Request):
    __tablename__ = "design_requests"

    id: Mapped[uuid.UUID] = mapped_column(ForeignKey("requests.id"), primary_key=True)
    subtype: Mapped[DesignRequestSubtype] = mapped_column(
        Enum(DesignRequestSubtype, name="design_request_subtype")
    )
    # Only meaningful for subtype=TEMPLATE (drives duty-rate lookup / margin
    # recommendation on the downstream pricing request).
    product_type_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("product_types.id"), nullable=True
    )
    design_project_number: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )
    lead_designer_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    dtp_designer_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    retailer_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("retailers.id"), nullable=True
    )
    requested_deadline: Mapped[date | None] = mapped_column(Date, nullable=True)
    # Colors the DTP designer needs to design for - a flat list, not
    # individually tracked (they're delivered together in one PDF/version).
    requested_colors: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    # Free-text creative brief from sales, plus the size/materials the
    # design needs to accommodate - capped at 4 materials (enforced in the
    # Pydantic schema, not here) since a design isn't produced in more.
    brief: Mapped[str | None] = mapped_column(Text, nullable=True)
    product_size: Mapped[str | None] = mapped_column(String(255), nullable=True)
    materials: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    status: Mapped[DesignRequestStatus] = mapped_column(
        Enum(DesignRequestStatus, name="design_request_status"),
        default=DesignRequestStatus.SUBMITTED,
    )
    # Which completed pricing request is currently authoritative when a
    # template has gone through multiple versions/quotes. use_alter breaks
    # the design_requests -> pricing_requests -> template_versions ->
    # design_requests table-creation cycle: this FK is added via a separate
    # ALTER TABLE after all three tables exist.
    leading_pricing_request_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey(
            "pricing_requests.id",
            use_alter=True,
            name="fk_design_requests_leading_pricing_request_id",
        ),
        nullable=True,
    )

    versions: Mapped[list["TemplateVersion"]] = relationship(
        back_populates="design_request",
        foreign_keys="TemplateVersion.design_request_id",
    )
    reference_materials: Mapped[list["ReferenceMaterial"]] = relationship(
        back_populates="design_request"
    )

    __mapper_args__ = {
        "polymorphic_identity": RequestCategory.DESIGN,
    }


class ReferenceMaterial(Base, UUIDPKMixin, TimestampMixin):
    """A file (logo, brand asset, inspiration image, ...) attached to a
    design request by sales at submission time - a request can have any
    number of these."""

    __tablename__ = "reference_materials"

    design_request_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("design_requests.id"))
    file_url: Mapped[str] = mapped_column(String(1024))
    original_filename: Mapped[str] = mapped_column(String(255))
    uploaded_by_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))

    design_request: Mapped["DesignRequest"] = relationship(back_populates="reference_materials")


class TemplateVersion(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "template_versions"

    design_request_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("design_requests.id")
    )
    version_number: Mapped[str] = mapped_column(String(20))
    pdf_url: Mapped[str] = mapped_column(String(1024))
    status: Mapped[TemplateVersionStatus] = mapped_column(
        Enum(TemplateVersionStatus, name="template_version_status"),
        default=TemplateVersionStatus.DRAFT,
    )
    trigger_reason: Mapped[TemplateVersionTrigger | None] = mapped_column(
        Enum(TemplateVersionTrigger, name="template_version_trigger"), nullable=True
    )

    design_request: Mapped["DesignRequest"] = relationship(
        back_populates="versions", foreign_keys=[design_request_id]
    )


class Comment(Base, UUIDPKMixin, TimestampMixin):
    """Generic note attached to any entity (e.g. design rejection feedback).

    entity_type/entity_id form a loose polymorphic reference (no DB-level FK,
    since it can point at different tables) rather than formal inheritance.
    """

    __tablename__ = "comments"

    entity_type: Mapped[str] = mapped_column(String(100))
    entity_id: Mapped[uuid.UUID]
    author_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    body: Mapped[str] = mapped_column(Text)
