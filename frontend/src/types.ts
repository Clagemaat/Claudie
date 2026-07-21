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
