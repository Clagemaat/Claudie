import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import NotificationChannel, NotificationType, Role, TaskStatus
from app.models.identity import User, UserRole
from app.models.ops import AuditLog, Notification, SLADefinition, Task

DEFAULT_SLA = timedelta(hours=24)


def now() -> datetime:
    return datetime.now(timezone.utc)


class TaskActionError(Exception):
    """Raised when someone tries to act on a task/request they're not
    allowed to (wrong assignee, wrong status, etc.)."""


def get_sla_duration(db: Session, entity_type: str, step_name: str) -> timedelta:
    sla = db.scalar(
        select(SLADefinition).where(
            SLADefinition.entity_type == entity_type,
            SLADefinition.step_name == step_name,
        )
    )
    return sla.duration if sla else DEFAULT_SLA


def create_task(
    db: Session,
    entity_type: str,
    entity_id: uuid.UUID,
    step_name: str,
    assigned_to_user_id: uuid.UUID | None = None,
    assigned_to_role: Role | None = None,
) -> Task:
    task = Task(
        entity_type=entity_type,
        entity_id=entity_id,
        step_name=step_name,
        assigned_to_user_id=assigned_to_user_id,
        assigned_to_role=assigned_to_role,
        due_at=now() + get_sla_duration(db, entity_type, step_name),
    )
    db.add(task)
    db.flush()

    if assigned_to_user_id is not None:
        notify_user(db, assigned_to_user_id, task.id, NotificationType.TASK_ASSIGNED)
    elif assigned_to_role is not None:
        notify_role(db, assigned_to_role, task.id, NotificationType.TASK_ASSIGNED)

    return task


def complete_tasks(db: Session, entity_type: str, entity_id: uuid.UUID, step_name: str) -> None:
    open_tasks = db.scalars(
        select(Task).where(
            Task.entity_type == entity_type,
            Task.entity_id == entity_id,
            Task.step_name == step_name,
            Task.status.in_([TaskStatus.OPEN, TaskStatus.ON_HOLD]),
        )
    ).all()
    for task in open_tasks:
        task.status = TaskStatus.DONE
        task.completed_at = now()


def hold_task(db: Session, task: Task, actor_id: uuid.UUID, reason: str) -> Task:
    if task.assigned_to_user_id != actor_id:
        raise TaskActionError("Only the assignee can put a task on hold")
    if task.status != TaskStatus.OPEN:
        raise TaskActionError("Only an open task can be put on hold")

    task.remaining_on_hold = task.due_at - now()
    task.hold_started_at = now()
    task.hold_reason = reason
    task.status = TaskStatus.ON_HOLD
    return task


def resume_task(db: Session, task: Task, actor_id: uuid.UUID) -> Task:
    if task.assigned_to_user_id != actor_id:
        raise TaskActionError("Only the assignee can resume a task")
    if task.status != TaskStatus.ON_HOLD:
        raise TaskActionError("Only an on-hold task can be resumed")

    task.due_at = now() + (task.remaining_on_hold or timedelta())
    task.hold_started_at = None
    task.remaining_on_hold = None
    task.hold_reason = None
    task.status = TaskStatus.OPEN
    return task


def notify_user(
    db: Session,
    user_id: uuid.UUID,
    task_id: uuid.UUID | None,
    notif_type: NotificationType,
    channel: NotificationChannel = NotificationChannel.EMAIL,
) -> Notification:
    notification = Notification(
        task_id=task_id, user_id=user_id, channel=channel, type=notif_type
    )
    db.add(notification)
    return notification


def notify_role(
    db: Session,
    role: Role,
    task_id: uuid.UUID | None,
    notif_type: NotificationType,
    channel: NotificationChannel = NotificationChannel.EMAIL,
) -> list[Notification]:
    user_ids = db.scalars(
        select(UserRole.user_id).where(UserRole.role == role)
    ).all()
    return [notify_user(db, user_id, task_id, notif_type, channel) for user_id in user_ids]


def audit(
    db: Session,
    entity_type: str,
    entity_id: uuid.UUID,
    action: str,
    performed_by: uuid.UUID,
    before: dict | None = None,
    after: dict | None = None,
    is_override: bool = False,
) -> AuditLog:
    entry = AuditLog(
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        performed_by=performed_by,
        before=before,
        after=after,
        is_override=is_override,
    )
    db.add(entry)
    return entry


def user_has_role(db: Session, user_id: uuid.UUID, role: Role) -> bool:
    return (
        db.scalar(
            select(UserRole).where(UserRole.user_id == user_id, UserRole.role == role)
        )
        is not None
    )
