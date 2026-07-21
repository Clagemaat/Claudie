import { useEffect, useState, type FormEvent } from 'react'
import { apiGet, apiPost } from '../api'
import { useOptions } from '../useOptions'
import { hasAnyRole, useSession } from '../session'
import type { Order, OrderDetail as OrderDetailType, PricingRequest, PricingRequestDetail, Project } from '../types'

interface OrdersPageProps {
  focusId?: string | null
  onFocusHandled?: () => void
}

export function OrdersPage({ focusId, onFocusHandled }: OrdersPageProps) {
  const [selectedId, setSelectedId] = useState<string | null>(null)

  useEffect(() => {
    if (focusId) {
      setSelectedId(focusId)
      onFocusHandled?.()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [focusId])

  if (selectedId) {
    return <OrderDetail id={selectedId} onBack={() => setSelectedId(null)} />
  }
  return <OrderList onOpen={setSelectedId} />
}

function OrderList({ onOpen }: { onOpen: (id: string) => void }) {
  const { user } = useSession()
  const [orders, setOrders] = useState<Order[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreate, setShowCreate] = useState(false)

  const load = async () => setOrders(await apiGet<Order[]>('/orders'))

  useEffect(() => {
    load().finally(() => setLoading(false))
  }, [])

  return (
    <section className="entity-manager">
      <h2>Orders</h2>
      {hasAnyRole(user, ['sales']) && (
        <>
          <button type="button" onClick={() => setShowCreate((s) => !s)}>
            {showCreate ? 'Cancel' : '+ New Order'}
          </button>
          {showCreate && (
            <CreateOrderForm
              onCreated={() => {
                setShowCreate(false)
                load()
              }}
            />
          )}
        </>
      )}
      {loading ? (
        <p>Loading…</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Status</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {orders.map((o) => (
              <tr key={o.id}>
                <td>{o.status}</td>
                <td>
                  <button type="button" onClick={() => onOpen(o.id)}>
                    Open
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  )
}

interface OrderableLine {
  quoteLineId: string
  label: string
}

function useOrderableLines(projectId: string): OrderableLine[] {
  const [lines, setLines] = useState<OrderableLine[]>([])

  useEffect(() => {
    if (!projectId) {
      setLines([])
      return
    }
    let cancelled = false
    apiGet<PricingRequest[]>('/pricing-requests').then(async (all) => {
      const candidates = all.filter((p) => p.project_id === projectId && p.source_type === 'template')
      const details = await Promise.all(
        candidates.map((p) => apiGet<PricingRequestDetail>(`/pricing-requests/${p.id}`)),
      )
      if (cancelled) return
      const opts: OrderableLine[] = []
      for (const d of details) {
        for (const line of d.lines) {
          if (line.status === 'priced') {
            opts.push({
              quoteLineId: line.id,
              label: `${line.color} · ${line.size} (qty quoted ${line.quantity}) - sell ${line.sell_price?.toFixed(2)}`,
            })
          }
        }
      }
      setLines(opts)
    })
    return () => {
      cancelled = true
    }
  }, [projectId])

  return lines
}

interface OrderLineDraft {
  quoteLineId: string
  label: string
  quantity: string
}

function CreateOrderForm({ onCreated }: { onCreated: () => void }) {
  const { user } = useSession()
  const projectOptions = useOptions<Project>('/projects', (p) => p.name)
  const [projectId, setProjectId] = useState('')
  const orderableLines = useOrderableLines(projectId)
  const [pickedLineId, setPickedLineId] = useState('')
  const [pickedQty, setPickedQty] = useState('')
  const [lines, setLines] = useState<OrderLineDraft[]>([])
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

  const addLine = () => {
    const found = orderableLines.find((l) => l.quoteLineId === pickedLineId)
    if (!found || !pickedQty) {
      setError('Pick a quote line and a quantity before adding.')
      return
    }
    setError(null)
    setLines((ls) => [...ls, { quoteLineId: found.quoteLineId, label: found.label, quantity: pickedQty }])
    setPickedLineId('')
    setPickedQty('')
  }

  const removeLine = (index: number) => setLines((ls) => ls.filter((_, i) => i !== index))

  const submit = async (e: FormEvent) => {
    e.preventDefault()
    if (!projectId || !user || lines.length === 0) {
      setError('Pick a project and add at least one line.')
      return
    }
    setSaving(true)
    setError(null)
    try {
      await apiPost(`/projects/${projectId}/orders`, {
        created_by_id: user.id,
        lines: lines.map((l) => ({ quote_line_id: l.quoteLineId, quantity_ordered: Number(l.quantity) })),
      })
      onCreated()
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
    } finally {
      setSaving(false)
    }
  }

  return (
    <form onSubmit={submit} className="entity-form" style={{ flexDirection: 'column', alignItems: 'stretch', maxWidth: 560 }}>
      <label>
        <span>Project</span>
        <select value={projectId} onChange={(e) => setProjectId(e.target.value)} required>
          <option value="">-- select --</option>
          {projectOptions.map((o) => (
            <option key={o.value} value={o.value}>
              {o.label}
            </option>
          ))}
        </select>
      </label>
      {projectId && orderableLines.length === 0 && (
        <p style={{ fontSize: 12 }}>No priced, template-based quote lines available to order on this project yet.</p>
      )}

      <h4>Lines to order</h4>
      {lines.length > 0 && (
        <table>
          <thead>
            <tr>
              <th>Line</th>
              <th>Qty ordered</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {lines.map((l, i) => (
              <tr key={i}>
                <td>{l.label}</td>
                <td>{l.quantity}</td>
                <td>
                  <button type="button" onClick={() => removeLine(i)}>
                    Remove
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      <div className="entity-form" style={{ padding: 0, border: 'none', background: 'none' }}>
        <label>
          <span>Quote line</span>
          <select value={pickedLineId} onChange={(e) => setPickedLineId(e.target.value)} disabled={!projectId}>
            <option value="">-- select --</option>
            {orderableLines.map((o) => (
              <option key={o.quoteLineId} value={o.quoteLineId}>
                {o.label}
              </option>
            ))}
          </select>
        </label>
        <label>
          <span>Quantity to order</span>
          <input type="number" value={pickedQty} onChange={(e) => setPickedQty(e.target.value)} />
        </label>
        <button type="button" onClick={addLine}>
          + Add line
        </button>
      </div>

      <button type="submit" disabled={saving} style={{ alignSelf: 'start', marginTop: 12 }}>
        {saving ? 'Saving…' : 'Create order'}
      </button>
      {error && <p className="error">{error}</p>}
    </form>
  )
}

function OrderDetail({ id, onBack }: { id: string; onBack: () => void }) {
  const [order, setOrder] = useState<OrderDetailType | null>(null)
  const [error, setError] = useState<string | null>(null)

  const load = async () => {
    try {
      setOrder(await apiGet<OrderDetailType>(`/orders/${id}`))
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
    }
  }

  useEffect(() => {
    load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id])

  if (!order) return <p>Loading…</p>

  return (
    <section className="entity-manager">
      <button type="button" onClick={onBack}>
        ← Back to list
      </button>
      <h2>Order · {order.status}</h2>
      <table>
        <thead>
          <tr>
            <th>Quantity ordered</th>
            <th>Item creation request</th>
          </tr>
        </thead>
        <tbody>
          {order.lines.map((l) => (
            <tr key={l.id}>
              <td>{l.quantity_ordered}</td>
              <td>{l.item_creation_request_id ?? '—'}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {error && <p className="error">{error}</p>}
    </section>
  )
}
