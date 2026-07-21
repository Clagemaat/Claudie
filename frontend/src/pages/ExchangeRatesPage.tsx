import { EntityManager, type FieldConfig } from '../components/EntityManager'
import type { ExchangeRate } from '../types'

const fields: FieldConfig[] = [
  { name: 'currency', label: 'Currency (e.g. USD)', type: 'text', required: true },
  { name: 'rate_to_eur', label: 'Rate to EUR', type: 'number', required: true },
  { name: 'effective_date', label: 'Effective date', type: 'date', required: true },
]

export function ExchangeRatesPage() {
  return (
    <EntityManager<ExchangeRate>
      title="Exchange Rates"
      listPath="/exchange-rates"
      createPath="/exchange-rates"
      fields={fields}
      columns={[
        { key: 'currency', label: 'Currency' },
        { key: 'rate_to_eur', label: 'Rate to EUR' },
        { key: 'effective_date', label: 'Effective date' },
      ]}
    />
  )
}
