import { EntityManager, type FieldConfig } from '../components/EntityManager'
import type { Location } from '../types'

const fields: FieldConfig[] = [{ name: 'name', label: 'Name', type: 'text', required: true }]

export function LocationsPage() {
  return (
    <EntityManager<Location>
      title="Locations"
      listPath="/locations"
      createPath="/locations"
      fields={fields}
      columns={[{ key: 'name', label: 'Name' }]}
    />
  )
}
