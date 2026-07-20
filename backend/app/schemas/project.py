import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import ProjectStatus


class ProjectCreate(BaseModel):
    name: str
    customer_id: uuid.UUID
    created_by_id: uuid.UUID


class ProjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    customer_id: uuid.UUID
    created_by_id: uuid.UUID
    status: ProjectStatus
    created_at: datetime
