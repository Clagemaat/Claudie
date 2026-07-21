import { useState } from 'react'
import { EntityManager, type FieldConfig } from '../components/EntityManager'
import type { Customer, Retailer } from '../types'

const customerFields: FieldConfig[] = [{ name: 'name', label: 'Name', type: 'text', required: true }]

const retailerFields: FieldConfig[] = [{ name: 'name', label: 'Name', type: 'text', required: true }]

export function CustomersPage() {
  const [selected, setSelected] = useState<Customer | null>(null)

  return (
    <>
      <EntityManager<Customer>
        title="Customers"
        listPath="/customers"
        createPath="/customers"
        fields={customerFields}
        columns={[
          { key: 'name', label: 'Name' },
          {
            key: 'retailers',
            label: 'Retailers',
            render: (c) => (
              <button type="button" onClick={() => setSelected(c)}>
                {selected?.id === c.id ? 'Managing…' : 'Manage retailers'}
              </button>
            ),
          },
        ]}
      />

      {selected && (
        <EntityManager<Retailer>
          title={`Retailers for ${selected.name}`}
          listPath={`/customers/${selected.id}/retailers`}
          createPath={`/customers/${selected.id}/retailers`}
          fields={retailerFields}
          columns={[{ key: 'name', label: 'Name' }]}
        />
      )}
    </>
  )
}
