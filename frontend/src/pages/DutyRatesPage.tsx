import { EntityManager, type FieldConfig } from '../components/EntityManager'
import { useOptions } from '../useOptions'
import type { DutyRate, Location } from '../types'

export function DutyRatesPage() {
  const locationOptions = useOptions<Location>('/locations', (l) => l.name)

  const fields: FieldConfig[] = [
    { name: 'hs_code', label: 'HS code', type: 'text', required: true, placeholder: 'e.g. 6109.10' },
    { name: 'destination_location_id', label: 'Destination', type: 'select', required: true, options: locationOptions },
    { name: 'rate_pct', label: 'Rate %', type: 'number', required: true },
  ]

  const locationName = (id: string) => locationOptions.find((o) => o.value === id)?.label ?? id

  return (
    <EntityManager<DutyRate>
      title="Duty Rates"
      listPath="/duty-rates"
      createPath="/duty-rates"
      fields={fields}
      columns={[
        { key: 'hs_code', label: 'HS code' },
        { key: 'destination_location_id', label: 'Destination', render: (r) => locationName(r.destination_location_id) },
        { key: 'rate_pct', label: 'Rate %' },
      ]}
    />
  )
}
