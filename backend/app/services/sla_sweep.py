from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import NotificationType, TaskStatus
from app.models.identity import UserRole
from app.models.ops import EscalationEvent, EscalationRule, Notification, SLADefinition, Task
from app.services.ops import notify_role, notify_user, now

DEFAULT_REMINDER_FREQUENCY = timedelta(hours=24)


def _get_reminder_frequency(db: Session, entity_type: str, step_name: str) -> timedelta:
    sla = db.scalar(
        select(SLADefinition).where(
            SLADefinition.entity_type == entity_type, SLADefinition.step_name == step_name
        )
    )
    return sla.reminder_frequency if sla else DEFAULT_REMINDER_FREQUENCY


def _maybe_send_reminder(db: Session, task: Task) -> bool:
    reminder_frequency = _get_reminder_frequency(db, task.entity_type, task.step_name)
    last_reminder = db.scalar(
        select(Notification)
        .where(Notification.task_id == task.id, Notification.type == NotificationType.SLA_REMINDER)
        .order_by(Notification.sent_at.desc())
    )
    if last_reminder is not None and (now() - last_reminder.sent_at) < reminder_frequency:
        return False

    if task.assigned_to_user_id is not None:
        notify_user(db, task.assigned_to_user_id, task.id, NotificationType.SLA_REMINDER)
    elif task.assigned_to_role is not None:
        notify_role(db, task.assigned_to_role, task.id, NotificationType.SLA_REMINDER)
    return True


def _maybe_escalate(db: Session, task: Task) -> bool:
    rule = db.scalar(
        select(EscalationRule).where(
            EscalationRule.entity_type == task.entity_type,
            EscalationRule.step_name == task.step_name,
        )
    )
    if rule is None or now() < task.due_at + rule.threshold_after_due:
        return False

    already_escalated = db.scalar(
        select(EscalationEvent).where(EscalationEvent.task_id == task.id)
    ) is not None
    if already_escalated:
        return False

    targets: list = []
    if rule.escalate_to_user_id is not None:
        targets = [rule.escalate_to_user_id]
    elif rule.escalate_to_role is not None:
        targets = db.scalars(
            select(UserRole.user_id).where(UserRole.role == rule.escalate_to_role)
        ).all()

    for user_id in targets:
        notify_user(db, user_id, task.id, NotificationType.ESCALATION)
        db.add(EscalationEvent(task_id=task.id, notified_user_id=user_id))
    return True


def run_sla_sweep(db: Session) -> dict:
    """Finds every open task past its due_at, sends an SLA reminder (rate
    limited by SLADefinition.reminder_frequency, or a 24h default) and,
    single-tier, escalates past EscalationRule.threshold_after_due exactly
    once per task. On-hold tasks are excluded - due_at only reflects time
    while actively open, per the pausable-clock design.

    Meant to run on a schedule (cron/celery-beat) in production; exposed
    here as a manually-triggerable endpoint since no scheduler is wired up
    in this environment yet.
    """
    overdue_tasks = db.scalars(
        select(Task).where(Task.status == TaskStatus.OPEN, Task.due_at < now())
    ).all()

    reminders_sent = 0
    escalations_fired = 0
    for task in overdue_tasks:
        if _maybe_send_reminder(db, task):
            reminders_sent += 1
        if _maybe_escalate(db, task):
            escalations_fired += 1

    db.commit()
    return {
        "tasks_checked": len(overdue_tasks),
        "reminders_sent": reminders_sent,
        "escalations_fired": escalations_fired,
    }
