import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.core import Project
from app.models.design import Comment, DesignRequest, ReferenceMaterial, TemplateVersion
from app.models.enums import DesignRequestStatus
from app.schemas.design import (
    DesignRequestCreate,
    DesignRequestDetailOut,
    DesignRequestOut,
    ReferenceMaterialOut,
    ReopenForRevisionRequest,
    ReviewDecisionRequest,
    SubmitForReviewRequest,
    TriageRequest,
)
from app.services import design_workflow
from app.services.file_storage import storage

router = APIRouter(tags=["design-requests"])


def _get_design_request(db: Session, design_request_id: uuid.UUID) -> DesignRequest:
    dr = db.get(DesignRequest, design_request_id)
    if dr is None:
        raise HTTPException(status_code=404, detail="design request not found")
    return dr


@router.get("/design-requests", response_model=list[DesignRequestOut])
def list_design_requests(
    status: DesignRequestStatus | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[DesignRequest]:
    """The consolidated overview for Traffic Manager - every design
    request and its status, not just the caller's own to-do list."""
    query = select(DesignRequest)
    if status is not None:
        query = query.where(DesignRequest.status == status)
    return db.scalars(query.order_by(DesignRequest.created_at)).all()


@router.post("/projects/{project_id}/design-requests", response_model=DesignRequestOut)
def create_design_request(
    project_id: uuid.UUID, payload: DesignRequestCreate, db: Session = Depends(get_db)
) -> DesignRequest:
    if db.get(Project, project_id) is None:
        raise HTTPException(status_code=404, detail="project not found")
    return design_workflow.create_design_request(db, project_id, payload)


@router.get("/design-requests/{design_request_id}", response_model=DesignRequestDetailOut)
def get_design_request(
    design_request_id: uuid.UUID, db: Session = Depends(get_db)
) -> DesignRequestDetailOut:
    dr = _get_design_request(db, design_request_id)
    versions = db.scalars(
        select(TemplateVersion)
        .where(TemplateVersion.design_request_id == dr.id)
        .order_by(TemplateVersion.created_at)
    ).all()
    comments = db.scalars(
        select(Comment)
        .where(Comment.entity_type == design_workflow.ENTITY_TYPE, Comment.entity_id == dr.id)
        .order_by(Comment.created_at)
    ).all()
    reference_materials = db.scalars(
        select(ReferenceMaterial)
        .where(ReferenceMaterial.design_request_id == dr.id)
        .order_by(ReferenceMaterial.created_at)
    ).all()
    return DesignRequestDetailOut(
        **DesignRequestOut.model_validate(dr).model_dump(),
        versions=versions,
        comments=comments,
        reference_materials=reference_materials,
    )


@router.post(
    "/design-requests/{design_request_id}/reference-materials",
    response_model=ReferenceMaterialOut,
)
async def upload_reference_material(
    design_request_id: uuid.UUID,
    uploaded_by_id: uuid.UUID = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> ReferenceMaterial:
    _get_design_request(db, design_request_id)
    content = await file.read()
    file_url = storage.save(file.filename, content)
    material = ReferenceMaterial(
        design_request_id=design_request_id,
        file_url=file_url,
        original_filename=file.filename,
        uploaded_by_id=uploaded_by_id,
    )
    db.add(material)
    db.commit()
    db.refresh(material)
    return material


@router.post("/design-requests/{design_request_id}/triage", response_model=DesignRequestOut)
def triage_design_request(
    design_request_id: uuid.UUID, payload: TriageRequest, db: Session = Depends(get_db)
) -> DesignRequest:
    dr = _get_design_request(db, design_request_id)
    try:
        return design_workflow.triage(db, dr, payload)
    except design_workflow.WorkflowError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post(
    "/design-requests/{design_request_id}/submit-for-review", response_model=DesignRequestOut
)
def submit_for_review(
    design_request_id: uuid.UUID, payload: SubmitForReviewRequest, db: Session = Depends(get_db)
) -> DesignRequest:
    dr = _get_design_request(db, design_request_id)
    try:
        return design_workflow.submit_for_review(db, dr, payload)
    except design_workflow.WorkflowError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/design-requests/{design_request_id}/review", response_model=DesignRequestOut)
def review_design_request(
    design_request_id: uuid.UUID, payload: ReviewDecisionRequest, db: Session = Depends(get_db)
) -> DesignRequest:
    dr = _get_design_request(db, design_request_id)
    try:
        return design_workflow.review_decision(db, dr, payload)
    except design_workflow.WorkflowError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post(
    "/design-requests/{design_request_id}/reopen-for-revision", response_model=DesignRequestOut
)
def reopen_design_request_for_revision(
    design_request_id: uuid.UUID, payload: ReopenForRevisionRequest, db: Session = Depends(get_db)
) -> DesignRequest:
    dr = _get_design_request(db, design_request_id)
    try:
        return design_workflow.reopen_for_revision(db, dr, payload)
    except design_workflow.WorkflowError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
