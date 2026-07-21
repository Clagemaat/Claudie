import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import false, or_, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.identity import User, UserRole
from app.models.ops import Task
from app.models.enums import TaskStatus
from app.schemas.task import TaskOut
from app.schemas.user import UserCreate, UserOut

router = APIRouter(prefix="/users", tags=["users"])


def _to_user_out(user: User) -> UserOut:
    return UserOut(
        id=user.id, name=user.name, email=user.email,
        roles=[ur.role for ur in user.roles],
    )


@router.post("", response_model=UserOut)
def create_user(payload: UserCreate, db: Session = Depends(get_db)) -> UserOut:
    user = User(name=payload.name, email=payload.email)
    db.add(user)
    db.flush()
    for role in payload.roles:
        db.add(UserRole(user_id=user.id, role=role))
    db.commit()
    db.refresh(user)
    return _to_user_out(user)


@router.get("", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db)) -> list[UserOut]:
    users = db.scalars(select(User).order_by(User.name)).all()
    return [_to_user_out(user) for user in users]


@router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: uuid.UUID, db: Session = Depends(get_db)) -> UserOut:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="user not found")
    return _to_user_out(user)


@router.get("/{user_id}/tasks", response_model=list[TaskOut])
def get_user_tasks(user_id: uuid.UUID, db: Session = Depends(get_db)) -> list[Task]:
    """A person's to-do list: open tasks assigned to them directly, plus
    unclaimed role-queue tasks for any role they hold."""
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="user not found")

    role_names = [ur.role for ur in user.roles]
    tasks = db.scalars(
        select(Task)
        .where(
            Task.status.in_([TaskStatus.OPEN, TaskStatus.ON_HOLD]),
            or_(
                Task.assigned_to_user_id == user_id,
                Task.assigned_to_role.in_(role_names) if role_names else false(),
            ),
        )
        .order_by(Task.due_at)
    ).all()
    return tasks
