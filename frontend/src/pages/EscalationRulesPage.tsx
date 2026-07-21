import { EntityManager, type FieldConfig } from '../components/EntityManager'
import { useOptions } from '../useOptions'
import { ENTITY_STEPS, ROLES, type EscalationRule, type User } from '../types'

export function EscalationRulesPage() {
  const userOptions = useOptions<User>('/users', (u) => `${u.name} (${u.email})`)

  const fields: FieldConfig[] = [
    { name: 'entity_step', label: 'Step', type: 'entity-step', required: true, options: ENTITY_STEPS },
    {
      name: 'threshold_after_due',
      label: 'Threshold past due (ISO 8601, e.g. PT24H = 24h)',
      type: 'text',
      required: true,
      placeholder: 'PT24H',
    },
    {
      name: 'escalate_to_role',
      label: 'Escalate to role (or pick a specific person below)',
      type: 'select',
      options: ROLES.map((r) => ({ value: r, label: r })),
    },
    {
      name: 'escalate_to_user_id',
      label: 'Escalate to specific person (overrides role)',
      type: 'select',
      options: userOptions,
    },
    { name: 'notify_message_template', label: 'Message', type: 'text', required: true },
  ]

  const userName = (id: string | null) => (id ? userOptions.find((o) => o.value === id)?.label ?? id : '—')

  return (
    <EntityManager<EscalationRule>
      title="Escalation Rules"
      listPath="/escalation-rules"
      createPath="/escalation-rules"
      fields={fields}
      columns={[
        { key: 'entity_type', label: 'Entity type' },
        { key: 'step_name', label: 'Step' },
        { key: 'threshold_after_due', label: 'Threshold' },
        { key: 'escalate_to_role', label: 'Role', render: (r) => r.escalate_to_role ?? '—' },
        { key: 'escalate_to_user_id', label: 'Person', render: (r) => userName(r.escalate_to_user_id) },
      ]}
    />
  )
}
