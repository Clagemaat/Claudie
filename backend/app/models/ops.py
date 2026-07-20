import uuid
from datetime import datetime, timedelta

from sqlalchemy import (
    JSON,
    DateTime,
    Enum,
    ForeignKey,
    Interval,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPKMixin
from app.models.enums import NotificationChannel, NotificationType, Role, TaskStatus


class Task(Base, UUIDPKMixin):
    """The to-do list engine: one row per step that currently needs a human
    action on some entity (DesignRequest, PricingRequest, ItemCreationRequest, ...).

    entity_type/entity_id is a loose polymorphic reference, not a DB-level FK,
    since it can point at several different tables.
    """

    __tablename__ = "tasks"

    entity_type: Mapped[str] = mapped_column(String(100))
    entity_id: Mapped[uuid.UUID]
    step_name: Mapped[str] = mapped_column(String(100))

    # Either a specific assignee, or an open role-queue item (e.g. "any
    # Costing person can claim this") - exactly one should be set at a time.
    assigned_to_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    assigned_to_role: Mapped[Role | None] = mapped_column(
        Enum(Role, name="role"), nullable=True
    )

    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus, name="task_status"), default=TaskStatus.OPEN
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    # Pausable-clock fields: only the assignee can hold a task, and holding
    # it freezes the remaining time until it's resumed rather than just
    # silencing reminders.
    hold_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    hold_started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    remaining_on_hold: Mapped[timedelta | None] = mapped_column(
        Interval, nullable=True
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class SLADefinition(Base, UUIDPKMixin):
    """Admin-maintained target duration per (entity_type, step_name)."""

    __tablename__ = "sla_definitions"
    __table_args__ = (
        UniqueConstraint("entity_type", "step_name", name="uq_sla_entity_step"),
    )

    entity_type: Mapped[str] = mapped_column(String(100))
    step_name: Mapped[str] = mapped_column(String(100))
    duration: Mapped[timedelta] = mapped_column(Interval)
    reminder_frequency: Mapped[timedelta] = mapped_column(Interval)


class EscalationRule(Base, UUIDPKMixin):
    """Single-tier escalation: if a task is still open this long past its
    due_at, notify someone beyond the assignee."""

    __tablename__ = "escalation_rules"
    __table_args__ = (
        UniqueConstraint(
            "entity_type", "step_name", name="uq_escalation_entity_step"
        ),
    )

    entity_type: Mapped[str] = mapped_column(String(100))
    step_name: Mapped[str] = mapped_column(String(100))
    threshold_after_due: Mapped[timedelta] = mapped_column(Interval)
    escalate_to_role: Mapped[Role | None] = mapped_column(
        Enum(Role, name="role"), nullable=True
    )
    escalate_to_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    notify_message_template: Mapped[str] = mapped_column(Text)


class EscalationEvent(Base, UUIDPKMixin):
    """Log of fired escalations, so the scheduled job never double-escalates
    the same task."""

    __tablename__ = "escalation_events"

    task_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tasks.id"))
    notified_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    triggered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Notification(Base, UUIDPKMixin):
    __tablename__ = "notifications"

    task_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("tasks.id"), nullable=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    channel: Mapped[NotificationChannel] = mapped_column(
        Enum(NotificationChannel, name="notification_channel")
    )
    type: Mapped[NotificationType] = mapped_column(
        Enum(NotificationType, name="notification_type")
    )
    sent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class AuditLog(Base, UUIDPKMixin):
    """Immutable log of every meaningful change, with is_override flagging
    actions a Sales Director took outside the normal flow."""

    __tablename__ = "audit_logs"

    entity_type: Mapped[str] = mapped_column(String(100))
    entity_id: Mapped[uuid.UUID]
    action: Mapped[str] = mapped_column(String(100))
    performed_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    is_override: Mapped[bool] = mapped_column(default=False)
    before: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    after: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
