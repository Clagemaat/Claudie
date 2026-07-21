import { EntityManager, type FieldConfig } from '../components/EntityManager'
import { useOptions } from '../useOptions'
import type { HandlingCost, ProductType } from '../types'

export function HandlingCostsPage() {
  const productTypeOptions = useOptions<ProductType>('/product-types', (p) => p.name)

  const fields: FieldConfig[] = [
    { name: 'product_type_id', label: 'Product type', type: 'select', required: true, options: productTypeOptions },
    { name: 'cost', label: 'Cost', type: 'number', required: true },
  ]

  const productTypeName = (id: string) => productTypeOptions.find((o) => o.value === id)?.label ?? id

  return (
    <EntityManager<HandlingCost>
      title="Handling Costs"
      listPath="/handling-costs"
      createPath="/handling-costs"
      fields={fields}
      columns={[
        { key: 'product_type_id', label: 'Product type', render: (r) => productTypeName(r.product_type_id) },
        { key: 'cost', label: 'Cost' },
      ]}
    />
  )
}
