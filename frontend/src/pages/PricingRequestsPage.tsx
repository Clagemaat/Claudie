import { useEffect, useState, type FormEvent } from 'react'
import { apiGet, apiPost } from '../api'
import { useOptions } from '../useOptions'
import { hasAnyRole, useSession } from '../session'
import type {
  DesignRequest,
  DesignRequestDetail,
  Location,
  PricingRequest,
  PricingRequestSourceType,
  Project,
  ProductType,
} from '../types'
import { PricingRequestDetailView } from './PricingRequestDetail'

interface PricingRequestsPageProps {
  focusId?: string | null
  onFocusHandled?: () => void
}

export function PricingRequestsPage({ focusId, onFocusHandled }: PricingRequestsPageProps) {
  const [selectedId, setSelectedId] = useState<string | null>(null)

  useEffect(() => {
    if (focusId) {
      setSelectedId(focusId)
      onFocusHandled?.()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [focusId])

  if (selectedId) {
    return <PricingRequestDetailView id={selectedId} onBack={() => setSelectedId(null)} />
  }
  return <PricingRequestList onOpen={setSelectedId} />
}

function PricingRequestList({ onOpen }: { onOpen: (id: string) => void }) {
  const { user } = useSession()
  const [requests, setRequests] = useState<PricingRequest[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreate, setShowCreate] = useState(false)

  const load = async () => setRequests(await apiGet<PricingRequest[]>('/pricing-requests'))

  useEffect(() => {
    load().finally(() => setLoading(false))
  }, [])

  return (
    <section className="entity-manager">
      <h2>Pricing Requests</h2>
      {hasAnyRole(user, ['sales']) && (
        <>
          <button type="button" onClick={() => setShowCreate((s) => !s)}>
            {showCreate ? 'Cancel' : '+ New Pricing Request'}
          </button>
          {showCreate && (
            <CreatePricingRequestForm
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
              <th>Source</th>
              <th>Status</th>
              <th>Assigned</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {requests.map((r) => (
              <tr key={r.id}>
                <td>{r.source_type}</td>
                <td>{r.status}</td>
                <td>{r.assigned_costing_user_id ? 'claimed' : 'unclaimed'}</td>
                <td>
                  <button type="button" onClick={() => onOpen(r.id)}>
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

interface LineDraft {
  color: string
  size: string
  quantity: string
  production_location_id: string
  delivery_location_id: string
}

const emptyLine: LineDraft = {
  color: '',
  size: '',
  quantity: '',
  production_location_id: '',
  delivery_location_id: '',
}

function useTemplateVersionOptions(projectId: string) {
  const [options, setOptions] = useState<{ value: string; label: string }[]>([])

  useEffect(() => {
    if (!projectId) {
      setOptions([])
      return
    }
    let cancelled = false
    apiGet<DesignRequest[]>('/design-requests').then(async (all) => {
      const candidates = all.filter(
        (d) => d.project_id === projectId && d.subtype === 'template' && d.status === 'approved',
      )
      const details = await Promise.all(
        candidates.map((d) => apiGet<DesignRequestDetail>(`/design-requests/${d.id}`)),
      )
      if (cancelled) return
      const opts: { value: string; label: string }[] = []
      for (const d of details) {
        for (const v of d.versions) {
          if (v.status === 'final_ready') {
            opts.push({ value: v.id, label: `${d.design_project_number ?? d.id.slice(0, 8)} · v${v.version_number}` })
          }
        }
      }
      setOptions(opts)
    })
    return () => {
      cancelled = true
    }
  }, [projectId])

  return options
}

function CreatePricingRequestForm({ onCreated }: { onCreated: () => void }) {
  const { user } = useSession()
  const projectOptions = useOptions<Project>('/projects', (p) => p.name)
  const productTypeOptions = useOptions<ProductType>('/product-types', (p) => p.name)
  const locationOptions = useOptions<Location>('/locations', (l) => l.name)

  const [projectId, setProjectId] = useState('')
  const [sourceType, setSourceType] = useState<PricingRequestSourceType>('template')
  const templateVersionOptions = useTemplateVersionOptions(projectId)
  const [templateVersionId, setTemplateVersionId] = useState('')
  const [productTypeId, setProductTypeId] = useState('')
  const [questionsNotes, setQuestionsNotes] = useState('')
  const [deliveryDate, setDeliveryDate] = useState('')
  const [quoteValidity, setQuoteValidity] = useState('')
  const [lines, setLines] = useState<LineDraft[]>([])
  const [draft, setDraft] = useState<LineDraft>(emptyLine)
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

  const addLine = () => {
    if (!draft.color || !draft.size || !draft.quantity || !draft.production_location_id || !draft.delivery_location_id) {
      setError('Fill in all line fields before adding.')
      return
    }
    setError(null)
    setLines((ls) => [...ls, draft])
    setDraft(emptyLine)
  }

  const removeLine = (index: number) => setLines((ls) => ls.filter((_, i) => i !== index))

  const locationName = (id: string) => locationOptions.find((o) => o.value === id)?.label ?? id

  const submit = async (e: FormEvent) => {
    e.preventDefault()
    if (!projectId || !user || lines.length === 0) {
      setError('Pick a project and add at least one line.')
      return
    }
    setSaving(true)
    setError(null)
    try {
      await apiPost(`/projects/${projectId}/pricing-requests`, {
        created_by_id: user.id,
        source_type: sourceType,
        template_version_id: sourceType === 'template' ? templateVersionId : undefined,
        product_type_id: sourceType === 'questions' ? productTypeId || undefined : undefined,
        questions: sourceType === 'questions' && questionsNotes ? { notes: questionsNotes } : undefined,
        requested_delivery_date: deliveryDate || undefined,
        requested_quote_validity_until: quoteValidity || undefined,
        lines: lines.map((l) => ({
          color: l.color,
          size: l.size,
          quantity: Number(l.quantity),
          production_location_id: l.production_location_id,
          delivery_location_id: l.delivery_location_id,
        })),
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
      <label>
        <span>Source</span>
        <select value={sourceType} onChange={(e) => setSourceType(e.target.value as PricingRequestSourceType)}>
          <option value="template">From an approved template</option>
          <option value="questions">Questions only (no template)</option>
        </select>
      </label>
      {sourceType === 'template' ? (
        <label>
          <span>Template version</span>
          <select value={templateVersionId} onChange={(e) => setTemplateVersionId(e.target.value)} required disabled={!projectId}>
            <option value="">-- select --</option>
            {templateVersionOptions.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
          {projectId && templateVersionOptions.length === 0 && (
            <span style={{ fontSize: 12 }}>No approved templates with a final-ready version on this project yet.</span>
          )}
        </label>
      ) : (
        <>
          <label>
            <span>Product type</span>
            <select value={productTypeId} onChange={(e) => setProductTypeId(e.target.value)} required>
              <option value="">-- select --</option>
              {productTypeOptions.map((o) => (
                <option key={o.value} value={o.value}>
                  {o.label}
                </option>
              ))}
            </select>
          </label>
          <label>
            <span>Questions / notes for Costing</span>
            <input type="text" value={questionsNotes} onChange={(e) => setQuestionsNotes(e.target.value)} />
          </label>
        </>
      )}
      <label>
        <span>Requested delivery date</span>
        <input type="date" value={deliveryDate} onChange={(e) => setDeliveryDate(e.target.value)} />
      </label>
      <label>
        <span>Quote must stay valid until</span>
        <input type="date" value={quoteValidity} onChange={(e) => setQuoteValidity(e.target.value)} />
      </label>

      <h4>Variations to quote</h4>
      {lines.length > 0 && (
        <table>
          <thead>
            <tr>
              <th>Color</th>
              <th>Size</th>
              <th>Qty</th>
              <th>Production</th>
              <th>Delivery</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {lines.map((l, i) => (
              <tr key={i}>
                <td>{l.color}</td>
                <td>{l.size}</td>
                <td>{l.quantity}</td>
                <td>{locationName(l.production_location_id)}</td>
                <td>{locationName(l.delivery_location_id)}</td>
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
          <span>Color</span>
          <input value={draft.color} onChange={(e) => setDraft((d) => ({ ...d, color: e.target.value }))} />
        </label>
        <label>
          <span>Size</span>
          <input value={draft.size} onChange={(e) => setDraft((d) => ({ ...d, size: e.target.value }))} />
        </label>
        <label>
          <span>Quantity</span>
          <input type="number" value={draft.quantity} onChange={(e) => setDraft((d) => ({ ...d, quantity: e.target.value }))} />
        </label>
        <label>
          <span>Production location</span>
          <select value={draft.production_location_id} onChange={(e) => setDraft((d) => ({ ...d, production_location_id: e.target.value }))}>
            <option value="">-- select --</option>
            {locationOptions.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
        </label>
        <label>
          <span>Delivery location</span>
          <select value={draft.delivery_location_id} onChange={(e) => setDraft((d) => ({ ...d, delivery_location_id: e.target.value }))}>
            <option value="">-- select --</option>
            {locationOptions.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
        </label>
        <button type="button" onClick={addLine}>
          + Add line
        </button>
      </div>

      <button type="submit" disabled={saving} style={{ alignSelf: 'start', marginTop: 12 }}>
        {saving ? 'Saving…' : 'Create pricing request'}
      </button>
      {error && <p className="error">{error}</p>}
    </form>
  )
}
