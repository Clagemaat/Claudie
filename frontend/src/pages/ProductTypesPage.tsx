import { EntityManager, type FieldConfig } from '../components/EntityManager'
import type { ProductType } from '../types'

const fields: FieldConfig[] = [{ name: 'name', label: 'Name', type: 'text', required: true }]

export function ProductTypesPage() {
  return (
    <EntityManager<ProductType>
      title="Product Types"
      listPath="/product-types"
      createPath="/product-types"
      fields={fields}
      columns={[{ key: 'name', label: 'Name' }]}
    />
  )
}
