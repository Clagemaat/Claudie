from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.design import Comment, DesignRequest, TemplateVersion
from app.models.enums import (
    DesignRequestStatus,
    NotificationType,
    RequestCategory,
    Role,
    TemplateVersionStatus,
    TemplateVersionTrigger,
)
from app.schemas.design import (
    DesignRequestCreate,
    ReopenForRevisionRequest,
    ReviewDecisionRequest,
    SubmitForReviewRequest,
    TriageRequest,
)
from app.services.ops import (
    audit,
    complete_tasks,
    create_task,
    notify_user,
    user_has_role,
)

ENTITY_TYPE = "design_request"


class WorkflowError(Exception):
    """A business-rule violation: wrong status, wrong actor, missing input."""


def create_design_request(db: Session, project_id, payload: DesignRequestCreate) -> DesignRequest:
    dr = DesignRequest(
        project_id=project_id,
        category=RequestCategory.DESIGN,
        created_by_id=payload.created_by_id,
        subtype=payload.subtype,
        product_type_id=payload.product_type_id,
        retailer_id=payload.retailer_id,
        requested_deadline=payload.requested_deadline,
        requested_colors=payload.requested_colors,
        brief=payload.brief,
        product_size=payload.product_size,
        materials=payload.materials,
        status=DesignRequestStatus.SUBMITTED,
    )
    db.add(dr)
    db.flush()

    create_task(db, ENTITY_TYPE, dr.id, "triage", assigned_to_role=Role.TRAFFIC_MANAGER)
    audit(
        db, ENTITY_TYPE, dr.id, "submitted", payload.created_by_id,
        after={"status": dr.status.value},
    )

    db.commit()
    db.refresh(dr)
    return dr


def triage(db: Session, dr: DesignRequest, payload: TriageRequest) -> DesignRequest:
    if dr.status != DesignRequestStatus.SUBMITTED:
        raise WorkflowError(f"cannot triage a request in status {dr.status.value}")
    if not user_has_role(db, payload.actor_id, Role.TRAFFIC_MANAGER):
        raise WorkflowError("actor must be a Traffic Manager")

    before = {"status": dr.status.value}
    dr.design_project_number = payload.design_project_number
    dr.lead_designer_id = payload.lead_designer_id
    dr.dtp_designer_id = payload.dtp_designer_id
    dr.status = DesignRequestStatus.IN_PROGRESS

    complete_tasks(db, ENTITY_TYPE, dr.id, "triage")
    create_task(db, ENTITY_TYPE, dr.id, "dtp_work", assigned_to_user_id=dr.dtp_designer_id)
    audit(
        db, ENTITY_TYPE, dr.id, "triaged", payload.actor_id,
        before=before, after={"status": dr.status.value},
    )

    db.commit()
    db.refresh(dr)
    return dr


def submit_for_review(
    db: Session, dr: DesignRequest, payload: SubmitForReviewRequest
) -> DesignRequest:
    if dr.status != DesignRequestStatus.IN_PROGRESS:
        raise WorkflowError(f"cannot submit for review from status {dr.status.value}")
    if dr.dtp_designer_id != payload.actor_id:
        raise WorkflowError("only the assigned DTP designer can submit work")

    draft = db.scalar(
        select(TemplateVersion).where(
            TemplateVersion.design_request_id == dr.id,
            TemplateVersion.status == TemplateVersionStatus.DRAFT,
        )
    )
    if draft is not None:
        # A rejected draft is replaced in place, not kept around.
        draft.pdf_url = payload.pdf_url
    else:
        existing_count = db.scalar(
            select(func.count()).select_from(TemplateVersion).where(
                TemplateVersion.design_request_id == dr.id
            )
        ) or 0
        draft = TemplateVersion(
            design_request_id=dr.id,
            version_number=f"{existing_count + 1}.0",
            pdf_url=payload.pdf_url,
            status=TemplateVersionStatus.DRAFT,
            trigger_reason=(
                payload.trigger_reason if existing_count > 0 else TemplateVersionTrigger.INITIAL
            ),
        )
        db.add(draft)

    before = {"status": dr.status.value}
    dr.status = DesignRequestStatus.IN_REVIEW

    complete_tasks(db, ENTITY_TYPE, dr.id, "dtp_work")
    # Either the lead designer or the traffic manager can approve - modeled
    # as two open tasks that both get closed the moment either is actioned.
    create_task(db, ENTITY_TYPE, dr.id, "review", assigned_to_user_id=dr.lead_designer_id)
    create_task(db, ENTITY_TYPE, dr.id, "review", assigned_to_role=Role.TRAFFIC_MANAGER)
    audit(
        db, ENTITY_TYPE, dr.id, "submitted_for_review", payload.actor_id,
        before=before, after={"status": dr.status.value},
    )

    db.commit()
    db.refresh(dr)
    return dr


def reopen_for_revision(
    db: Session, dr: DesignRequest, payload: ReopenForRevisionRequest
) -> DesignRequest:
    """The post-pricing "customer wants a change" / "someone spotted a
    mistake" case - re-enters at In Progress with the same design project #,
    lead designer, and DTP designer (no re-triage). The actual version
    trigger_reason (customer_change vs mistake_fix) is recorded when the
    DTP designer submits the revised work, same as the initial version."""
    if dr.status != DesignRequestStatus.APPROVED:
        raise WorkflowError(f"cannot reopen a request in status {dr.status.value}")

    is_requester = dr.created_by_id == payload.actor_id
    is_traffic_manager = user_has_role(db, payload.actor_id, Role.TRAFFIC_MANAGER)
    if not (is_requester or is_traffic_manager):
        raise WorkflowError("actor must be the original requester or a traffic manager")

    before = {"status": dr.status.value}
    dr.status = DesignRequestStatus.IN_PROGRESS

    db.add(Comment(
        entity_type=ENTITY_TYPE, entity_id=dr.id,
        author_id=payload.actor_id, body=payload.reason,
    ))
    create_task(db, ENTITY_TYPE, dr.id, "dtp_work", assigned_to_user_id=dr.dtp_designer_id)
    audit(
        db, ENTITY_TYPE, dr.id, "reopened_for_revision", payload.actor_id,
        before=before, after={"status": dr.status.value},
    )

    db.commit()
    db.refresh(dr)
    return dr


def review_decision(
    db: Session, dr: DesignRequest, payload: ReviewDecisionRequest
) -> DesignRequest:
    if dr.status != DesignRequestStatus.IN_REVIEW:
        raise WorkflowError(f"cannot review a request in status {dr.status.value}")

    is_lead_designer = dr.lead_designer_id == payload.actor_id
    is_traffic_manager = user_has_role(db, payload.actor_id, Role.TRAFFIC_MANAGER)
    if not (is_lead_designer or is_traffic_manager):
        raise WorkflowError("actor must be the lead designer or a traffic manager")

    complete_tasks(db, ENTITY_TYPE, dr.id, "review")
    before = {"status": dr.status.value}

    if payload.decision == "approve":
        draft = db.scalar(
            select(TemplateVersion).where(
                TemplateVersion.design_request_id == dr.id,
                TemplateVersion.status == TemplateVersionStatus.DRAFT,
            )
        )
        if draft is not None:
            draft.status = TemplateVersionStatus.FINAL_READY
        dr.status = DesignRequestStatus.APPROVED
        notify_user(db, dr.created_by_id, None, NotificationType.APPROVED)
        audit(
            db, ENTITY_TYPE, dr.id, "approved", payload.actor_id,
            before=before, after={"status": dr.status.value},
        )
    else:
        if not payload.comment:
            raise WorkflowError("a comment is required when rejecting")
        db.add(Comment(
            entity_type=ENTITY_TYPE, entity_id=dr.id,
            author_id=payload.actor_id, body=payload.comment,
        ))
        dr.status = DesignRequestStatus.IN_PROGRESS
        create_task(db, ENTITY_TYPE, dr.id, "dtp_work", assigned_to_user_id=dr.dtp_designer_id)
        notify_user(db, dr.dtp_designer_id, None, NotificationType.REJECTED)
        audit(
            db, ENTITY_TYPE, dr.id, "rejected", payload.actor_id,
            before=before, after={"status": dr.status.value},
        )

    db.commit()
    db.refresh(dr)
    return dr
