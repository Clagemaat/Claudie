import { EntityManager, type FieldConfig } from '../components/EntityManager'
import { useOptions } from '../useOptions'
import type { FreightRate, Location } from '../types'

export function FreightRatesPage() {
  const locationOptions = useOptions<Location>('/locations', (l) => l.name)

  const fields: FieldConfig[] = [
    { name: 'production_location_id', label: 'Production location', type: 'select', required: true, options: locationOptions },
    { name: 'delivery_location_id', label: 'Delivery location', type: 'select', required: true, options: locationOptions },
    { name: 'cost_per_cbm', label: 'Cost per cbm', type: 'number', required: true },
  ]

  const locationName = (id: string) => locationOptions.find((o) => o.value === id)?.label ?? id

  return (
    <EntityManager<FreightRate>
      title="Freight Rates"
      listPath="/freight-rates"
      createPath="/freight-rates"
      fields={fields}
      columns={[
        { key: 'production_location_id', label: 'Production', render: (r) => locationName(r.production_location_id) },
        { key: 'delivery_location_id', label: 'Delivery', render: (r) => locationName(r.delivery_location_id) },
        { key: 'cost_per_cbm', label: 'Cost / cbm' },
      ]}
    />
  )
}
