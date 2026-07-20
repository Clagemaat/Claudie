import enum


class Role(str, enum.Enum):
    SALES = "sales"
    TRAFFIC_MANAGER = "traffic_manager"
    LEAD_DESIGNER = "lead_designer"
    DTP_DESIGNER = "dtp_designer"
    COSTING = "costing"
    SALES_DIRECTOR = "sales_director"
    ITEM_CREATOR = "item_creator"
    ADMIN = "admin"


class ProjectStatus(str, enum.Enum):
    OPEN = "open"
    CLOSED = "closed"


class RequestCategory(str, enum.Enum):
    """Polymorphic discriminator for the Request base table."""

    DESIGN = "design"
    PRICING = "pricing"


class DesignRequestSubtype(str, enum.Enum):
    PRESENTATION = "presentation"
    TEMPLATE = "template"
    MOCKUP = "mockup"


class DesignRequestStatus(str, enum.Enum):
    SUBMITTED = "submitted"
    TRIAGED = "triaged"
    IN_PROGRESS = "in_progress"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"


class TemplateVersionStatus(str, enum.Enum):
    DRAFT = "draft"
    FINAL_READY = "final_ready"


class TemplateVersionTrigger(str, enum.Enum):
    INITIAL = "initial"
    CUSTOMER_CHANGE = "customer_change"
    MISTAKE_FIX = "mistake_fix"


class PricingRequestSourceType(str, enum.Enum):
    TEMPLATE = "template"
    QUESTIONS = "questions"


class PricingRequestStatus(str, enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    COMPLETE = "complete"


class QuoteLineStatus(str, enum.Enum):
    REQUESTED = "requested"
    PRICED = "priced"


class OrderStatus(str, enum.Enum):
    PENDING_ITEM_CREATION = "pending_item_creation"
    READY = "ready"


class ItemCreationStatus(str, enum.Enum):
    PENDING = "pending"
    DONE = "done"


class TaskStatus(str, enum.Enum):
    OPEN = "open"
    ON_HOLD = "on_hold"
    DONE = "done"


class NotificationChannel(str, enum.Enum):
    EMAIL = "email"
    IN_APP = "in_app"


class NotificationType(str, enum.Enum):
    TASK_ASSIGNED = "task_assigned"
    SLA_REMINDER = "sla_reminder"
    ESCALATION = "escalation"
    REJECTED = "rejected"
    APPROVED = "approved"
