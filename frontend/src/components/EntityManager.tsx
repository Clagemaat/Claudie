import { useEffect, useState, type FormEvent } from 'react'
import { apiGet, apiPost } from '../api'
import type { WithId } from '../types'

export type FieldType = 'text' | 'number' | 'date' | 'select' | 'multiselect' | 'entity-step'

export interface FieldOption {
  value: string
  label: string
}

export interface FieldConfig {
  name: string
  label: string
  type: FieldType
  required?: boolean
  options?: FieldOption[]
  placeholder?: string
}

export interface ColumnConfig<T> {
  key: string
  label: string
  render?: (row: T) => React.ReactNode
}

interface EntityManagerProps<T extends WithId> {
  title: string
  listPath: string
  createPath: string
  fields: FieldConfig[]
  columns: ColumnConfig<T>[]
  onCreated?: (created: T) => void
  /** Extra payload fields not shown as form inputs (e.g. created_by_id
   * derived from the signed-in user rather than typed by them). */
  extraPayload?: Record<string, unknown>
}

export function EntityManager<T extends WithId>({
  title,
  listPath,
  createPath,
  fields,
  columns,
  onCreated,
  extraPayload,
}: EntityManagerProps<T>) {
  const [rows, setRows] = useState<T[]>([])
  const [form, setForm] = useState<Record<string, string | string[]>>({})
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [loadingList, setLoadingList] = useState(true)

  const load = async () => {
    setLoadingList(true)
    try {
      setRows(await apiGet<T[]>(listPath))
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
    } finally {
      setLoadingList(false)
    }
  }

  useEffect(() => {
    load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [listPath])

  const handleChange = (name: string, value: string | string[]) => {
    setForm((f) => ({ ...f, [name]: value }))
  }

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      const payload: Record<string, unknown> = { ...extraPayload }
      for (const field of fields) {
        const raw = form[field.name]
        if (raw === undefined || raw === '' || (Array.isArray(raw) && raw.length === 0)) continue

        if (field.type === 'entity-step') {
          const [entityType, stepName] = String(raw).split('|')
          payload.entity_type = entityType
          payload.step_name = stepName
        } else if (field.type === 'number') {
          payload[field.name] = Number(raw)
        } else {
          payload[field.name] = raw
        }
      }
      const created = await apiPost<T>(createPath, payload)
      setForm({})
      await load()
      onCreated?.(created)
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <section className="entity-manager">
      <h2>{title}</h2>
      <form onSubmit={handleSubmit} className="entity-form">
        {fields.map((field) => (
          <label key={field.name}>
            <span>{field.label}</span>
            {field.type === 'select' || field.type === 'entity-step' ? (
              <select
                value={(form[field.name] as string) ?? ''}
                onChange={(e) => handleChange(field.name, e.target.value)}
                required={field.required}
              >
                <option value="">-- select --</option>
                {field.options?.map((o) => (
                  <option key={o.value} value={o.value}>
                    {o.label}
                  </option>
                ))}
              </select>
            ) : field.type === 'multiselect' ? (
              <select
                multiple
                value={(form[field.name] as string[]) ?? []}
                onChange={(e) =>
                  handleChange(
                    field.name,
                    Array.from(e.target.selectedOptions).map((o) => o.value),
                  )
                }
              >
                {field.options?.map((o) => (
                  <option key={o.value} value={o.value}>
                    {o.label}
                  </option>
                ))}
              </select>
            ) : (
              <input
                type={field.type === 'number' ? 'number' : field.type === 'date' ? 'date' : 'text'}
                step={field.type === 'number' ? 'any' : undefined}
                value={(form[field.name] as string) ?? ''}
                onChange={(e) => handleChange(field.name, e.target.value)}
                required={field.required}
                placeholder={field.placeholder}
              />
            )}
          </label>
        ))}
        <button type="submit" disabled={loading}>
          {loading ? 'Saving…' : 'Add'}
        </button>
      </form>
      {error && <p className="error">{error}</p>}
      <table>
        <thead>
          <tr>
            {columns.map((c) => (
              <th key={c.key}>{c.label}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {loadingList ? (
            <tr>
              <td colSpan={columns.length}>Loading…</td>
            </tr>
          ) : rows.length === 0 ? (
            <tr>
              <td colSpan={columns.length}>Nothing yet.</td>
            </tr>
          ) : (
            rows.map((row) => (
              <tr key={row.id}>
                {columns.map((c) => (
                  <td key={c.key}>{c.render ? c.render(row) : String((row as Record<string, unknown>)[c.key] ?? '')}</td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </section>
  )
}
