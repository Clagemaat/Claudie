from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.core import Location, ProductType
from app.models.reference_data import DutyRate, ExchangeRate, FreightRate, HandlingCost
from app.schemas.reference_data import (
    DutyRateCreate,
    DutyRateOut,
    ExchangeRateCreate,
    ExchangeRateOut,
    FreightRateCreate,
    FreightRateOut,
    HandlingCostCreate,
    HandlingCostOut,
    LocationCreate,
    LocationOut,
    ProductTypeCreate,
    ProductTypeOut,
)

router = APIRouter(tags=["reference-data"])


@router.post("/locations", response_model=LocationOut)
def create_location(payload: LocationCreate, db: Session = Depends(get_db)) -> Location:
    location = Location(name=payload.name)
    db.add(location)
    db.commit()
    db.refresh(location)
    return location


@router.get("/locations", response_model=list[LocationOut])
def list_locations(db: Session = Depends(get_db)) -> list[Location]:
    return db.scalars(select(Location)).all()


@router.post("/product-types", response_model=ProductTypeOut)
def create_product_type(payload: ProductTypeCreate, db: Session = Depends(get_db)) -> ProductType:
    product_type = ProductType(name=payload.name)
    db.add(product_type)
    db.commit()
    db.refresh(product_type)
    return product_type


@router.get("/product-types", response_model=list[ProductTypeOut])
def list_product_types(db: Session = Depends(get_db)) -> list[ProductType]:
    return db.scalars(select(ProductType)).all()


@router.post("/exchange-rates", response_model=ExchangeRateOut)
def create_exchange_rate(
    payload: ExchangeRateCreate, db: Session = Depends(get_db)
) -> ExchangeRate:
    rate = ExchangeRate(**payload.model_dump())
    db.add(rate)
    db.commit()
    db.refresh(rate)
    return rate


@router.get("/exchange-rates", response_model=list[ExchangeRateOut])
def list_exchange_rates(db: Session = Depends(get_db)) -> list[ExchangeRate]:
    return db.scalars(select(ExchangeRate)).all()


@router.post("/freight-rates", response_model=FreightRateOut)
def create_freight_rate(payload: FreightRateCreate, db: Session = Depends(get_db)) -> FreightRate:
    rate = FreightRate(**payload.model_dump())
    db.add(rate)
    db.commit()
    db.refresh(rate)
    return rate


@router.get("/freight-rates", response_model=list[FreightRateOut])
def list_freight_rates(db: Session = Depends(get_db)) -> list[FreightRate]:
    return db.scalars(select(FreightRate)).all()


@router.post("/duty-rates", response_model=DutyRateOut)
def create_duty_rate(payload: DutyRateCreate, db: Session = Depends(get_db)) -> DutyRate:
    rate = DutyRate(**payload.model_dump())
    db.add(rate)
    db.commit()
    db.refresh(rate)
    return rate


@router.get("/duty-rates", response_model=list[DutyRateOut])
def list_duty_rates(db: Session = Depends(get_db)) -> list[DutyRate]:
    return db.scalars(select(DutyRate)).all()


@router.post("/handling-costs", response_model=HandlingCostOut)
def create_handling_cost(
    payload: HandlingCostCreate, db: Session = Depends(get_db)
) -> HandlingCost:
    cost = HandlingCost(**payload.model_dump())
    db.add(cost)
    db.commit()
    db.refresh(cost)
    return cost


@router.get("/handling-costs", response_model=list[HandlingCostOut])
def list_handling_costs(db: Session = Depends(get_db)) -> list[HandlingCost]:
    return db.scalars(select(HandlingCost)).all()
