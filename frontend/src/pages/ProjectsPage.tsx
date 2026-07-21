import { EntityManager, type FieldConfig } from '../components/EntityManager'
import { useOptions } from '../useOptions'
import { useSession } from '../session'
import type { Customer, Project } from '../types'

interface ProjectsPageProps {
  onOpenProject?: (id: string) => void
}

export function ProjectsPage({ onOpenProject }: ProjectsPageProps) {
  const { user } = useSession()
  const customerOptions = useOptions<Customer>('/customers', (c) => c.name)

  const fields: FieldConfig[] = [
    { name: 'name', label: 'Project name', type: 'text', required: true },
    { name: 'customer_id', label: 'Customer', type: 'select', required: true, options: customerOptions },
  ]

  const customerName = (id: string) => customerOptions.find((o) => o.value === id)?.label ?? id

  return (
    <EntityManager<Project>
      title="Projects"
      listPath="/projects"
      createPath="/projects"
      fields={fields}
      // created_by_id comes from the signed-in user, not a form field
      extraPayload={{ created_by_id: user?.id }}
      columns={[
        {
          key: 'name',
          label: 'Name',
          render: (p) =>
            onOpenProject ? (
              <button type="button" onClick={() => onOpenProject(p.id)}>
                {p.name}
              </button>
            ) : (
              p.name
            ),
        },
        { key: 'customer_id', label: 'Customer', render: (p) => customerName(p.customer_id) },
        { key: 'status', label: 'Status' },
      ]}
    />
  )
}
