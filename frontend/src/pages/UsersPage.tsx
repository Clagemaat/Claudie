import { EntityManager, type FieldConfig } from '../components/EntityManager'
import { ROLES, type User } from '../types'

const fields: FieldConfig[] = [
  { name: 'name', label: 'Name', type: 'text', required: true },
  { name: 'email', label: 'Email', type: 'text', required: true },
  {
    name: 'roles',
    label: 'Roles (ctrl/cmd-click for multiple)',
    type: 'multiselect',
    options: ROLES.map((r) => ({ value: r, label: r })),
  },
]

export function UsersPage() {
  return (
    <EntityManager<User>
      title="Users"
      listPath="/users"
      createPath="/users"
      fields={fields}
      columns={[
        { key: 'name', label: 'Name' },
        { key: 'email', label: 'Email' },
        { key: 'roles', label: 'Roles', render: (u) => u.roles.join(', ') || '—' },
      ]}
    />
  )
}
