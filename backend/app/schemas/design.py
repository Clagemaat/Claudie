import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

from app.models.enums import (
    DesignRequestStatus,
    DesignRequestSubtype,
    TemplateVersionStatus,
    TemplateVersionTrigger,
)


class DesignRequestCreate(BaseModel):
    subtype: DesignRequestSubtype
    product_type_id: uuid.UUID | None = None
    retailer_id: uuid.UUID | None = None
    requested_deadline: date | None = None
    requested_colors: list[str] | None = None
    created_by_id: uuid.UUID


class TriageRequest(BaseModel):
    actor_id: uuid.UUID
    design_project_number: str
    lead_designer_id: uuid.UUID
    dtp_designer_id: uuid.UUID


class SubmitForReviewRequest(BaseModel):
    actor_id: uuid.UUID
    pdf_url: str
    # Only meaningful when this submission starts a new version after a
    # prior version was already approved (i.e. a post-pricing revision).
    trigger_reason: TemplateVersionTrigger | None = None


class ReviewDecisionRequest(BaseModel):
    actor_id: uuid.UUID
    decision: Literal["approve", "reject"]
    comment: str | None = None


class TemplateVersionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    version_number: str
    pdf_url: str
    status: TemplateVersionStatus
    trigger_reason: TemplateVersionTrigger | None
    created_at: datetime


class CommentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    author_id: uuid.UUID
    body: str
    created_at: datetime


class ReferenceMaterialOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    file_url: str
    original_filename: str
    uploaded_by_id: uuid.UUID
    created_at: datetime


class DesignRequestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    subtype: DesignRequestSubtype
    product_type_id: uuid.UUID | None
    retailer_id: uuid.UUID | None
    requested_deadline: date | None
    requested_colors: list[str] | None
    design_project_number: str | None
    lead_designer_id: uuid.UUID | None
    dtp_designer_id: uuid.UUID | None
    status: DesignRequestStatus
    leading_pricing_request_id: uuid.UUID | None
    created_by_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class DesignRequestDetailOut(DesignRequestOut):
    versions: list[TemplateVersionOut] = []
    comments: list[CommentOut] = []
    reference_materials: list[ReferenceMaterialOut] = []
