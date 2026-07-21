import { useEffect, useState } from 'react'
import { apiGet, apiPost } from '../api'
import { useSession } from '../session'
import type { Task } from '../types'

interface MyTasksPageProps {
  onOpenDesignRequest?: (id: string) => void
  onOpenPricingRequest?: (id: string) => void
}

function formatDue(task: Task): string {
  if (task.status === 'on_hold') return 'On hold'
  const due = new Date(task.due_at)
  const now = new Date()
  const diffMs = due.getTime() - now.getTime()
  const overdue = diffMs < 0
  const hours = Math.abs(Math.round(diffMs / 3_600_000))
  return overdue ? `Overdue by ~${hours}h` : `Due in ~${hours}h`
}

export function MyTasksPage({ onOpenDesignRequest, onOpenPricingRequest }: MyTasksPageProps) {
  const { user } = useSession()
  const [tasks, setTasks] = useState<Task[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [holdReason, setHoldReason] = useState<Record<string, string>>({})

  const load = async () => {
    if (!user) return
    setLoading(true)
    try {
      setTasks(await apiGet<Task[]>(`/users/${user.id}/tasks`))
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user?.id])

  const hold = async (task: Task) => {
    const reason = holdReason[task.id]
    if (!reason) {
      setError('Enter a reason before putting a task on hold.')
      return
    }
    setError(null)
    try {
      await apiPost(`/tasks/${task.id}/hold`, { actor_id: user!.id, reason })
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
    }
  }

  const resume = async (task: Task) => {
    setError(null)
    try {
      await apiPost(`/tasks/${task.id}/resume`, { actor_id: user!.id })
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
    }
  }

  const label = (task: Task) => `${task.entity_type.replace('_', ' ')} → ${task.step_name.replace('_', ' ')}`

  return (
    <section className="entity-manager">
      <h2>My Tasks</h2>
      {error && <p className="error">{error}</p>}
      {loading ? (
        <p>Loading…</p>
      ) : tasks.length === 0 ? (
        <p>Nothing on your plate right now.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Step</th>
              <th>Status</th>
              <th>Due</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {tasks.map((task) => (
              <tr key={task.id}>
                <td>
                  {task.entity_type === 'design_request' && onOpenDesignRequest ? (
                    <button type="button" onClick={() => onOpenDesignRequest(task.entity_id)}>
                      {label(task)}
                    </button>
                  ) : task.entity_type === 'pricing_request' && onOpenPricingRequest ? (
                    <button type="button" onClick={() => onOpenPricingRequest(task.entity_id)}>
                      {label(task)}
                    </button>
                  ) : (
                    label(task)
                  )}
                </td>
                <td>{task.status}{task.assigned_to_role && !task.assigned_to_user_id ? ' (unclaimed)' : ''}</td>
                <td>{formatDue(task)}</td>
                <td>
                  {task.status === 'open' && task.assigned_to_user_id === user?.id && (
                    <div className="task-hold-row">
                      <input
                        type="text"
                        placeholder="Hold reason"
                        value={holdReason[task.id] ?? ''}
                        onChange={(e) => setHoldReason((h) => ({ ...h, [task.id]: e.target.value }))}
                      />
                      <button type="button" onClick={() => hold(task)}>
                        Hold
                      </button>
                    </div>
                  )}
                  {task.status === 'on_hold' && task.assigned_to_user_id === user?.id && (
                    <button type="button" onClick={() => resume(task)}>
                      Resume
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  )
}
