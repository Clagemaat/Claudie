"""Import every model module so Base.metadata is fully populated before
Alembic autogenerate or Base.metadata.create_all() runs."""

from app.models.base import Base
from app.models.core import Customer, Location, Project, ProductType, Retailer
from app.models.costing import Factory, FactoryQuoteOption, PricingRequest, QuoteLine
from app.models.design import (
    Comment,
    DesignRequest,
    ReferenceMaterial,
    Request,
    TemplateVersion,
)
from app.models.fulfillment import ItemCreationRequest, Order, OrderLine
from app.models.identity import User, UserRole
from app.models.ops import (
    AuditLog,
    EscalationEvent,
    EscalationRule,
    Notification,
    SLADefinition,
    Task,
)
from app.models.reference_data import DutyRate, ExchangeRate, FreightRate, HandlingCost

__all__ = [
    "Base",
    "Customer",
    "Location",
    "Project",
    "ProductType",
    "Retailer",
    "Factory",
    "FactoryQuoteOption",
    "PricingRequest",
    "QuoteLine",
    "Comment",
    "DesignRequest",
    "ReferenceMaterial",
    "Request",
    "TemplateVersion",
    "ItemCreationRequest",
    "Order",
    "OrderLine",
    "User",
    "UserRole",
    "AuditLog",
    "EscalationEvent",
    "EscalationRule",
    "Notification",
    "SLADefinition",
    "Task",
    "DutyRate",
    "ExchangeRate",
    "FreightRate",
    "HandlingCost",
]
