import uuid

from pydantic import BaseModel, ConfigDict

from app.models.enums import Role


class UserCreate(BaseModel):
    name: str
    email: str
    roles: list[Role] = []


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    email: str
    roles: list[Role] = []


class CustomerCreate(BaseModel):
    name: str


class CustomerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str


class RetailerCreate(BaseModel):
    name: str


class RetailerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    customer_id: uuid.UUID
    name: str
