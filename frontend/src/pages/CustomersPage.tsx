import { useEffect, useState } from 'react'
import { apiGet } from '../api'
import { EntityManager, type FieldConfig, type FieldOption } from '../components/EntityManager'
import type { Customer, Retailer } from '../types'

const customerFields: FieldConfig[] = [{ name: 'name', label: 'Name', type: 'text', required: true }]

export function CustomersPage() {
  const [customerOptions, setCustomerOptions] = useState<FieldOption[]>([])

  const loadCustomerOptions = async () => {
    const customers = await apiGet<Customer[]>('/customers')
    setCustomerOptions(customers.map((c) => ({ value: c.id, label: c.name })))
  }

  useEffect(() => {
    loadCustomerOptions()
  }, [])

  const customerName = (id: string) => customerOptions.find((o) => o.value === id)?.label ?? id

  const retailerFields: FieldConfig[] = [
    { name: 'customer_id', label: 'Customer', type: 'select', required: true, options: customerOptions },
    { name: 'name', label: 'Name', type: 'text', required: true },
  ]

  return (
    <>
      <EntityManager<Customer>
        title="Customers"
        listPath="/customers"
        createPath="/customers"
        fields={customerFields}
        columns={[{ key: 'name', label: 'Name' }]}
        onCreated={loadCustomerOptions}
      />

      {/* Retailers are managed as their own independent list here -
          creating one just requires picking any existing customer from
          the dropdown, not first drilling into that customer's page. */}
      <EntityManager<Retailer>
        title="Retailers"
        listPath="/retailers"
        createPath="/retailers"
        fields={retailerFields}
        columns={[
          { key: 'customer_id', label: 'Customer', render: (r) => customerName(r.customer_id) },
          { key: 'name', label: 'Name' },
        ]}
      />
    </>
  )
}
