import uuid
from datetime import datetime, timedelta

from pydantic import BaseModel, ConfigDict

from app.models.enums import Role, TaskStatus


class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    entity_type: str
    entity_id: uuid.UUID
    step_name: str
    assigned_to_user_id: uuid.UUID | None
    assigned_to_role: Role | None
    status: TaskStatus
    created_at: datetime
    due_at: datetime
    hold_reason: str | None
    hold_started_at: datetime | None
    remaining_on_hold: timedelta | None
    completed_at: datetime | None


class HoldRequest(BaseModel):
    actor_id: uuid.UUID
    reason: str


class ResumeRequest(BaseModel):
    actor_id: uuid.UUID
