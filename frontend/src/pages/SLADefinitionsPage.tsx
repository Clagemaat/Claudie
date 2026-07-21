import { EntityManager, type FieldConfig } from '../components/EntityManager'
import { ENTITY_STEPS, type SLADefinition } from '../types'

const fields: FieldConfig[] = [
  { name: 'entity_step', label: 'Step', type: 'entity-step', required: true, options: ENTITY_STEPS },
  {
    name: 'duration',
    label: 'SLA duration (ISO 8601, e.g. PT4H = 4h, P1D = 1 day)',
    type: 'text',
    required: true,
    placeholder: 'PT4H',
  },
  {
    name: 'reminder_frequency',
    label: 'Reminder frequency (ISO 8601)',
    type: 'text',
    required: true,
    placeholder: 'PT24H',
  },
]

export function SLADefinitionsPage() {
  return (
    <EntityManager<SLADefinition>
      title="SLA Definitions"
      listPath="/sla-definitions"
      createPath="/sla-definitions"
      fields={fields}
      columns={[
        { key: 'entity_type', label: 'Entity type' },
        { key: 'step_name', label: 'Step' },
        { key: 'duration', label: 'Duration' },
        { key: 'reminder_frequency', label: 'Reminder frequency' },
      ]}
    />
  )
}
