import { useEffect, useState, type FormEvent } from 'react'
import { apiGet, apiPost, uploadFile } from '../api'
import { useOptions } from '../useOptions'
import { hasAnyRole, useSession } from '../session'
import type {
  DesignRequest,
  DesignRequestDetail as DesignRequestDetailType,
  DesignRequestSubtype,
  ProductType,
  Project,
  Retailer,
  User,
} from '../types'

interface DesignRequestsPageProps {
  focusId?: string | null
  onFocusHandled?: () => void
}

export function DesignRequestsPage({ focusId, onFocusHandled }: DesignRequestsPageProps) {
  const [selectedId, setSelectedId] = useState<string | null>(null)

  useEffect(() => {
    if (focusId) {
      setSelectedId(focusId)
      onFocusHandled?.()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [focusId])

  if (selectedId) {
    return <DesignRequestDetail id={selectedId} onBack={() => setSelectedId(null)} />
  }
  return <DesignRequestList onOpen={setSelectedId} />
}

function DesignRequestList({ onOpen }: { onOpen: (id: string) => void }) {
  const { user } = useSession()
  const [requests, setRequests] = useState<DesignRequest[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreate, setShowCreate] = useState(false)

  const load = async () => setRequests(await apiGet<DesignRequest[]>('/design-requests'))

  useEffect(() => {
    load().finally(() => setLoading(false))
  }, [])

  return (
    <section className="entity-manager">
      <h2>Design Requests</h2>
      {hasAnyRole(user, ['sales']) && (
        <>
          <button type="button" onClick={() => setShowCreate((s) => !s)}>
            {showCreate ? 'Cancel' : '+ New Design Request'}
          </button>
          {showCreate && (
            <CreateDesignRequestForm
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
              <th>Subtype</th>
              <th>Status</th>
              <th>Project #</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {requests.map((r) => (
              <tr key={r.id}>
                <td>{r.subtype}</td>
                <td>{r.status}</td>
                <td>{r.design_project_number ?? '—'}</td>
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

function CreateDesignRequestForm({ onCreated }: { onCreated: () => void }) {
  const { user } = useSession()
  const projectOptions = useOptions<Project>('/projects', (p) => p.name)
  const productTypeOptions = useOptions<ProductType>('/product-types', (p) => p.name)
  const [projectId, setProjectId] = useState('')
  const [subtype, setSubtype] = useState<DesignRequestSubtype>('template')
  const [productTypeId, setProductTypeId] = useState('')
  const [retailerId, setRetailerId] = useState('')
  const [retailerOptions, setRetailerOptions] = useState<{ value: string; label: string }[]>([])
  const [deadline, setDeadline] = useState('')
  const [colors, setColors] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (!projectId) {
      setRetailerOptions([])
      return
    }
    apiGet<Project>(`/projects/${projectId}`).then((project) =>
      apiGet<Retailer[]>(`/customers/${project.customer_id}/retailers`).then((retailers) =>
        setRetailerOptions(retailers.map((r) => ({ value: r.id, label: r.name }))),
      ),
    )
  }, [projectId])

  const submit = async (e: FormEvent) => {
    e.preventDefault()
    if (!projectId || !user) return
    setSaving(true)
    setError(null)
    try {
      await apiPost(`/projects/${projectId}/design-requests`, {
        subtype,
        product_type_id: productTypeId || undefined,
        retailer_id: retailerId || undefined,
        requested_deadline: deadline || undefined,
        requested_colors: colors ? colors.split(',').map((c) => c.trim()).filter(Boolean) : undefined,
        created_by_id: user.id,
      })
      onCreated()
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
    } finally {
      setSaving(false)
    }
  }

  return (
    <form onSubmit={submit} className="entity-form">
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
        <span>Subtype</span>
        <select value={subtype} onChange={(e) => setSubtype(e.target.value as DesignRequestSubtype)}>
          <option value="template">Template</option>
          <option value="presentation">Presentation</option>
          <option value="mockup">Mockup</option>
        </select>
      </label>
      <label>
        <span>Product type</span>
        <select value={productTypeId} onChange={(e) => setProductTypeId(e.target.value)}>
          <option value="">-- none --</option>
          {productTypeOptions.map((o) => (
            <option key={o.value} value={o.value}>
              {o.label}
            </option>
          ))}
        </select>
      </label>
      <label>
        <span>Retailer</span>
        <select value={retailerId} onChange={(e) => setRetailerId(e.target.value)} disabled={!projectId}>
          <option value="">-- none --</option>
          {retailerOptions.map((o) => (
            <option key={o.value} value={o.value}>
              {o.label}
            </option>
          ))}
        </select>
      </label>
      <label>
        <span>Requested deadline</span>
        <input type="date" value={deadline} onChange={(e) => setDeadline(e.target.value)} />
      </label>
      <label>
        <span>Requested colors (comma-separated)</span>
        <input
          type="text"
          value={colors}
          onChange={(e) => setColors(e.target.value)}
          placeholder="Red, Blue, Forest Green"
        />
      </label>
      <button type="submit" disabled={saving}>
        {saving ? 'Saving…' : 'Create'}
      </button>
      {error && <p className="error">{error}</p>}
    </form>
  )
}

function DesignRequestDetail({ id, onBack }: { id: string; onBack: () => void }) {
  const { user } = useSession()
  const [dr, setDr] = useState<DesignRequestDetailType | null>(null)
  const [error, setError] = useState<string | null>(null)

  const load = async () => {
    try {
      setDr(await apiGet<DesignRequestDetailType>(`/design-requests/${id}`))
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
    }
  }

  useEffect(() => {
    load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id])

  if (!dr) return <p>Loading…</p>

  const canTriage = dr.status === 'submitted' && hasAnyRole(user, ['traffic_manager'])
  const canSubmit = dr.status === 'in_progress' && user?.id === dr.dtp_designer_id
  const canReview =
    dr.status === 'in_review' &&
    (user?.id === dr.lead_designer_id || hasAnyRole(user, ['traffic_manager']))
  const canReopen =
    dr.status === 'approved' && (user?.id === dr.created_by_id || hasAnyRole(user, ['traffic_manager']))

  return (
    <section className="entity-manager">
      <button type="button" onClick={onBack}>
        ← Back to list
      </button>
      <h2>
        Design Request · {dr.subtype} · {dr.status}
      </h2>
      <table className="detail-table">
        <tbody>
          <tr>
            <th>Design project #</th>
            <td>{dr.design_project_number ?? '—'}</td>
          </tr>
          <tr>
            <th>Requested deadline</th>
            <td>{dr.requested_deadline ?? '—'}</td>
          </tr>
          <tr>
            <th>Requested colors</th>
            <td>{dr.requested_colors?.join(', ') ?? '—'}</td>
          </tr>
        </tbody>
      </table>

      <h3>Versions</h3>
      {dr.versions.length === 0 ? (
        <p>None yet.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Version</th>
              <th>Status</th>
              <th>Trigger</th>
              <th>PDF</th>
            </tr>
          </thead>
          <tbody>
            {dr.versions.map((v) => (
              <tr key={v.id}>
                <td>{v.version_number}</td>
                <td>{v.status}</td>
                <td>{v.trigger_reason ?? '—'}</td>
                <td>
                  <a href={v.pdf_url} target="_blank" rel="noreferrer">
                    View
                  </a>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <h3>Reference materials</h3>
      {dr.reference_materials.length === 0 ? (
        <p>None uploaded.</p>
      ) : (
        <ul>
          {dr.reference_materials.map((m) => (
            <li key={m.id}>
              <a href={m.file_url} target="_blank" rel="noreferrer">
                {m.original_filename}
              </a>
            </li>
          ))}
        </ul>
      )}

      <h3>Comments</h3>
      {dr.comments.length === 0 ? (
        <p>None yet.</p>
      ) : (
        <ul>
          {dr.comments.map((c) => (
            <li key={c.id}>{c.body}</li>
          ))}
        </ul>
      )}

      {canTriage && <TriageForm designRequestId={dr.id} onDone={load} />}
      {canSubmit && <SubmitForReviewForm designRequestId={dr.id} hasEarlierVersion={dr.versions.length > 0} onDone={load} />}
      {canReview && <ReviewForm designRequestId={dr.id} onDone={load} />}
      {canReopen && <ReopenForm designRequestId={dr.id} onDone={load} />}
      {error && <p className="error">{error}</p>}
    </section>
  )
}

function TriageForm({ designRequestId, onDone }: { designRequestId: string; onDone: () => void }) {
  const { user } = useSession()
  const [users, setUsers] = useState<User[]>([])
  const [designProjectNumber, setDesignProjectNumber] = useState('')
  const [leadDesignerId, setLeadDesignerId] = useState('')
  const [dtpDesignerId, setDtpDesignerId] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    apiGet<User[]>('/users').then(setUsers)
  }, [])

  const leadOptions = users.filter((u) => u.roles.includes('lead_designer'))
  const dtpOptions = users.filter((u) => u.roles.includes('dtp_designer'))

  const submit = async (e: FormEvent) => {
    e.preventDefault()
    if (!user) return
    setSaving(true)
    setError(null)
    try {
      await apiPost(`/design-requests/${designRequestId}/triage`, {
        actor_id: user.id,
        design_project_number: designProjectNumber,
        lead_designer_id: leadDesignerId,
        dtp_designer_id: dtpDesignerId,
      })
      onDone()
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
    } finally {
      setSaving(false)
    }
  }

  return (
    <form onSubmit={submit} className="entity-form action-form">
      <h4>Triage</h4>
      <label>
        <span>Design project #</span>
        <input value={designProjectNumber} onChange={(e) => setDesignProjectNumber(e.target.value)} required />
      </label>
      <label>
        <span>Lead designer</span>
        <select value={leadDesignerId} onChange={(e) => setLeadDesignerId(e.target.value)} required>
          <option value="">-- select --</option>
          {leadOptions.map((u) => (
            <option key={u.id} value={u.id}>
              {u.name}
            </option>
          ))}
        </select>
      </label>
      <label>
        <span>DTP designer</span>
        <select value={dtpDesignerId} onChange={(e) => setDtpDesignerId(e.target.value)} required>
          <option value="">-- select --</option>
          {dtpOptions.map((u) => (
            <option key={u.id} value={u.id}>
              {u.name}
            </option>
          ))}
        </select>
      </label>
      <button type="submit" disabled={saving}>
        {saving ? 'Saving…' : 'Assign'}
      </button>
      {error && <p className="error">{error}</p>}
    </form>
  )
}

function SubmitForReviewForm({
  designRequestId,
  hasEarlierVersion,
  onDone,
}: {
  designRequestId: string
  hasEarlierVersion: boolean
  onDone: () => void
}) {
  const { user } = useSession()
  const [file, setFile] = useState<File | null>(null)
  const [triggerReason, setTriggerReason] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

  const submit = async (e: FormEvent) => {
    e.preventDefault()
    if (!user || !file) return
    setSaving(true)
    setError(null)
    try {
      const pdfUrl = await uploadFile(file)
      await apiPost(`/design-requests/${designRequestId}/submit-for-review`, {
        actor_id: user.id,
        pdf_url: pdfUrl,
        trigger_reason: triggerReason || undefined,
      })
      onDone()
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
    } finally {
      setSaving(false)
    }
  }

  return (
    <form onSubmit={submit} className="entity-form action-form">
      <h4>Submit work for review</h4>
      <label>
        <span>PDF file</span>
        <input type="file" onChange={(e) => setFile(e.target.files?.[0] ?? null)} required />
      </label>
      {hasEarlierVersion && (
        <label>
          <span>Reason for this revision</span>
          <select value={triggerReason} onChange={(e) => setTriggerReason(e.target.value)}>
            <option value="">-- n/a --</option>
            <option value="customer_change">Customer requested change</option>
            <option value="mistake_fix">Fixing a mistake</option>
          </select>
        </label>
      )}
      <button type="submit" disabled={saving}>
        {saving ? 'Uploading…' : 'Submit'}
      </button>
      {error && <p className="error">{error}</p>}
    </form>
  )
}

function ReviewForm({ designRequestId, onDone }: { designRequestId: string; onDone: () => void }) {
  const { user } = useSession()
  const [comment, setComment] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

  const decide = async (decision: 'approve' | 'reject') => {
    if (!user) return
    if (decision === 'reject' && !comment) {
      setError('A comment is required when rejecting.')
      return
    }
    setSaving(true)
    setError(null)
    try {
      await apiPost(`/design-requests/${designRequestId}/review`, {
        actor_id: user.id,
        decision,
        comment: comment || undefined,
      })
      onDone()
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="entity-form action-form">
      <h4>Review</h4>
      <label>
        <span>Comment (required to reject)</span>
        <input value={comment} onChange={(e) => setComment(e.target.value)} />
      </label>
      <button type="button" onClick={() => decide('approve')} disabled={saving}>
        Approve
      </button>
      <button type="button" onClick={() => decide('reject')} disabled={saving}>
        Reject
      </button>
      {error && <p className="error">{error}</p>}
    </div>
  )
}

function ReopenForm({ designRequestId, onDone }: { designRequestId: string; onDone: () => void }) {
  const { user } = useSession()
  const [reason, setReason] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

  const submit = async (e: FormEvent) => {
    e.preventDefault()
    if (!user) return
    setSaving(true)
    setError(null)
    try {
      await apiPost(`/design-requests/${designRequestId}/reopen-for-revision`, {
        actor_id: user.id,
        reason,
      })
      onDone()
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
    } finally {
      setSaving(false)
    }
  }

  return (
    <form onSubmit={submit} className="entity-form action-form">
      <h4>Reopen for a new version</h4>
      <label>
        <span>Reason</span>
        <input value={reason} onChange={(e) => setReason(e.target.value)} required />
      </label>
      <button type="submit" disabled={saving}>
        {saving ? 'Saving…' : 'Reopen'}
      </button>
      {error && <p className="error">{error}</p>}
    </form>
  )
}
