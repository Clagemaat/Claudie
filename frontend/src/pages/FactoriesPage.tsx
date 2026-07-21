import { EntityManager, type FieldConfig } from '../components/EntityManager'
import type { Factory } from '../types'

const fields: FieldConfig[] = [
  { name: 'name', label: 'Name', type: 'text', required: true },
  { name: 'contact_info', label: 'Contact info', type: 'text' },
]

export function FactoriesPage() {
  return (
    <EntityManager<Factory>
      title="Factories"
      listPath="/factories"
      createPath="/factories"
      fields={fields}
      columns={[
        { key: 'name', label: 'Name' },
        { key: 'contact_info', label: 'Contact info', render: (f) => f.contact_info ?? '—' },
      ]}
    />
  )
}
