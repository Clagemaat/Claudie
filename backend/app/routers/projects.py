import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.core import Customer, Project, Retailer
from app.schemas.project import ProjectCreate, ProjectOut
from app.schemas.user import (
    CustomerCreate,
    CustomerOut,
    RetailerCreate,
    RetailerCreateWithCustomer,
    RetailerOut,
)

router = APIRouter(tags=["projects"])


@router.post("/customers", response_model=CustomerOut)
def create_customer(payload: CustomerCreate, db: Session = Depends(get_db)) -> Customer:
    customer = Customer(name=payload.name)
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


@router.get("/customers", response_model=list[CustomerOut])
def list_customers(db: Session = Depends(get_db)) -> list[Customer]:
    return db.scalars(select(Customer)).all()


@router.post("/customers/{customer_id}/retailers", response_model=RetailerOut)
def create_retailer(
    customer_id: uuid.UUID, payload: RetailerCreate, db: Session = Depends(get_db)
) -> Retailer:
    if db.get(Customer, customer_id) is None:
        raise HTTPException(status_code=404, detail="customer not found")
    retailer = Retailer(customer_id=customer_id, name=payload.name)
    db.add(retailer)
    db.commit()
    db.refresh(retailer)
    return retailer


@router.get("/customers/{customer_id}/retailers", response_model=list[RetailerOut])
def list_retailers(customer_id: uuid.UUID, db: Session = Depends(get_db)) -> list[Retailer]:
    return db.scalars(select(Retailer).where(Retailer.customer_id == customer_id)).all()


@router.post("/retailers", response_model=RetailerOut)
def create_retailer_flat(
    payload: RetailerCreateWithCustomer, db: Session = Depends(get_db)
) -> Retailer:
    """Same as create_retailer, but for the standalone Retailers screen -
    the customer is picked from a dropdown there instead of being implied
    by which customer's page you're already on."""
    if db.get(Customer, payload.customer_id) is None:
        raise HTTPException(status_code=404, detail="customer not found")
    retailer = Retailer(customer_id=payload.customer_id, name=payload.name)
    db.add(retailer)
    db.commit()
    db.refresh(retailer)
    return retailer


@router.get("/retailers", response_model=list[RetailerOut])
def list_retailers_flat(db: Session = Depends(get_db)) -> list[Retailer]:
    return db.scalars(select(Retailer)).all()


@router.post("/projects", response_model=ProjectOut)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db)) -> Project:
    project = Project(
        name=payload.name,
        customer_id=payload.customer_id,
        created_by_id=payload.created_by_id,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.get("/projects", response_model=list[ProjectOut])
def list_projects(db: Session = Depends(get_db)) -> list[Project]:
    return db.scalars(select(Project).order_by(Project.created_at)).all()


@router.get("/projects/{project_id}", response_model=ProjectOut)
def get_project(project_id: uuid.UUID, db: Session = Depends(get_db)) -> Project:
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="project not found")
    return project
