export const ROLES = [
  'sales',
  'traffic_manager',
  'lead_designer',
  'dtp_designer',
  'costing',
  'sales_director',
  'item_creator',
  'admin',
] as const

export type Role = (typeof ROLES)[number]

export interface WithId {
  id: string
}

export interface User extends WithId {
  name: string
  email: string
  roles: Role[]
}

export interface Customer extends WithId {
  name: string
}

export interface Retailer extends WithId {
  customer_id: string
  name: string
}

export interface Location extends WithId {
  name: string
}

export interface ProductType extends WithId {
  name: string
}

export interface Factory extends WithId {
  name: string
  contact_info: string | null
}

export interface ExchangeRate extends WithId {
  currency: string
  rate_to_eur: number
  effective_date: string
}

export interface FreightRate extends WithId {
  production_location_id: string
  delivery_location_id: string
  cost_per_cbm: number
}

export interface DutyRate extends WithId {
  hs_code: string
  destination_location_id: string
  rate_pct: number
}

export interface HandlingCost extends WithId {
  product_type_id: string
  cost: number
}

export interface SLADefinition extends WithId {
  entity_type: string
  step_name: string
  duration: string
  reminder_frequency: string
}

export interface EscalationRule extends WithId {
  entity_type: string
  step_name: string
  threshold_after_due: string
  escalate_to_role: Role | null
  escalate_to_user_id: string | null
  notify_message_template: string
}

export interface Task extends WithId {
  entity_type: string
  entity_id: string
  step_name: string
  assigned_to_user_id: string | null
  assigned_to_role: Role | null
  status: 'open' | 'on_hold' | 'done'
  created_at: string
  due_at: string
  hold_reason: string | null
  hold_started_at: string | null
  remaining_on_hold: string | null
  completed_at: string | null
}

export interface Project extends WithId {
  name: string
  customer_id: string
  created_by_id: string
  status: 'open' | 'closed'
  created_at: string
}

export type DesignRequestSubtype = 'presentation' | 'template' | 'mockup'
export type DesignRequestStatus = 'submitted' | 'triaged' | 'in_progress' | 'in_review' | 'approved' | 'rejected'

export interface DesignRequest extends WithId {
  project_id: string
  subtype: DesignRequestSubtype
  product_type_id: string | null
  retailer_id: string | null
  requested_deadline: string | null
  requested_colors: string[] | null
  brief: string | null
  product_size: string | null
  materials: string[] | null
  design_project_number: string | null
  lead_designer_id: string | null
  dtp_designer_id: string | null
  status: DesignRequestStatus
  leading_pricing_request_id: string | null
  created_by_id: string
  created_at: string
  updated_at: string
}

export interface TemplateVersion extends WithId {
  version_number: string
  pdf_url: string
  status: 'draft' | 'final_ready'
  trigger_reason: 'initial' | 'customer_change' | 'mistake_fix' | null
  created_at: string
}

export interface Comment extends WithId {
  author_id: string
  body: string
  created_at: string
}

export interface ReferenceMaterial extends WithId {
  file_url: string
  original_filename: string
  uploaded_by_id: string
  created_at: string
}

export interface DesignRequestDetail extends DesignRequest {
  versions: TemplateVersion[]
  comments: Comment[]
  reference_materials: ReferenceMaterial[]
}

export type PricingRequestSourceType = 'template' | 'questions'
export type PricingRequestStatus = 'open' | 'in_progress' | 'complete'
export type QuoteLineStatus = 'requested' | 'priced'

export interface PricingRequest extends WithId {
  project_id: string
  source_type: PricingRequestSourceType
  template_version_id: string | null
  product_type_id: string | null
  questions: Record<string, unknown> | null
  requested_delivery_date: string | null
  requested_quote_validity_until: string | null
  assigned_costing_user_id: string | null
  status: PricingRequestStatus
  created_by_id: string
  created_at: string
  updated_at: string
}

export interface QuoteLine extends WithId {
  pricing_request_id: string
  color: string
  size: string
  quantity: number
  production_location_id: string
  delivery_location_id: string
  status: QuoteLineStatus
  factory_id: string | null
  hs_code: string | null
  purchase_price: number | null
  purchase_currency: string | null
  fx_rate_to_eur: number | null
  box_width_cm: number | null
  box_length_cm: number | null
  box_height_cm: number | null
  box_qty: number | null
  volume_cbm: number | null
  freight_cost: number | null
  duty_cost: number | null
  handling_cost: number | null
  landed_cost: number | null
  margin_pct: number | null
  sell_price: number | null
}

export interface PricingRequestDetail extends PricingRequest {
  lines: QuoteLine[]
}

export interface FactoryQuoteOption extends WithId {
  quote_line_id: string
  factory_id: string
  quoted_price: number
  currency: string
  notes: string | null
  is_selected: boolean
  landed_cost: number | null
}

export interface MarginRecommendation {
  recommended_margin_pct: number | null
  based_on_count: number
}

export type OrderStatus = 'pending_item_creation' | 'ready'
export type ItemCreationStatus = 'pending' | 'done'

export interface OrderLine extends WithId {
  order_id: string
  quote_line_id: string
  quantity_ordered: number
  item_creation_request_id: string | null
}

export interface Order extends WithId {
  project_id: string
  customer_id: string
  created_by_id: string
  status: OrderStatus
  created_at: string
  updated_at: string
}

export interface OrderDetail extends Order {
  lines: OrderLine[]
}

export interface ItemCreationRequest extends WithId {
  design_request_id: string
  color: string
  size: string
  status: ItemCreationStatus
  assigned_item_creator_id: string | null
  erp_item_number: string | null
  created_at: string
  completed_at: string | null
}

// Known (entity_type, step_name) pairs a Task can actually be created with -
// keeping this a dropdown (rather than free text) avoids SLA/escalation
// rules silently never matching anything due to a typo.
export const ENTITY_STEPS: { value: string; label: string }[] = [
  { value: 'design_request|triage', label: 'Design Request → Triage' },
  { value: 'design_request|dtp_work', label: 'Design Request → DTP Work' },
  { value: 'design_request|review', label: 'Design Request → Review' },
  { value: 'pricing_request|claim', label: 'Pricing Request → Claim' },
  { value: 'pricing_request|pricing', label: 'Pricing Request → Pricing' },
  { value: 'item_creation_request|create_item', label: 'Item Creation → Create Item' },
]
