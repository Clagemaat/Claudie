from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.sla_sweep import run_sla_sweep

router = APIRouter(tags=["ops"])


@router.post("/ops/sla-sweep")
def sla_sweep(db: Session = Depends(get_db)) -> dict:
    return run_sla_sweep(db)
