import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.ops import Task
from app.schemas.task import HoldRequest, ResumeRequest, TaskOut
from app.services import ops

router = APIRouter(prefix="/tasks", tags=["tasks"])


def _get_task(db: Session, task_id: uuid.UUID) -> Task:
    task = db.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="task not found")
    return task


@router.post("/{task_id}/hold", response_model=TaskOut)
def hold_task(task_id: uuid.UUID, payload: HoldRequest, db: Session = Depends(get_db)) -> Task:
    task = _get_task(db, task_id)
    try:
        ops.hold_task(db, task, payload.actor_id, payload.reason)
    except ops.TaskActionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    db.commit()
    db.refresh(task)
    return task


@router.post("/{task_id}/resume", response_model=TaskOut)
def resume_task(task_id: uuid.UUID, payload: ResumeRequest, db: Session = Depends(get_db)) -> Task:
    task = _get_task(db, task_id)
    try:
        ops.resume_task(db, task, payload.actor_id)
    except ops.TaskActionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    db.commit()
    db.refresh(task)
    return task
