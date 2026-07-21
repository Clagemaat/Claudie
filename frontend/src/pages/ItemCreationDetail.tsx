import { useEffect, useState, type FormEvent } from 'react'
import { apiGet, apiPost } from '../api'
import { hasAnyRole, useSession } from '../session'
import type { ItemCreationRequest } from '../types'

export function ItemCreationDetail({ id, onBack }: { id: string; onBack: () => void }) {
  const { user } = useSession()
  const [item, setItem] = useState<ItemCreationRequest | null>(null)
  const [erpItemNumber, setErpItemNumber] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

  const load = async () => {
    try {
      setItem(await apiGet<ItemCreationRequest>(`/item-creation-requests/${id}`))
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
    }
  }

  useEffect(() => {
    load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id])

  if (!item) return <p>Loading…</p>

  const canComplete = item.status === 'pending' && hasAnyRole(user, ['item_creator'])

  const submit = async (e: FormEvent) => {
    e.preventDefault()
    if (!user || !erpItemNumber) return
    setSaving(true)
    setError(null)
    try {
      await apiPost(`/item-creation-requests/${item.id}/complete`, {
        actor_id: user.id,
        erp_item_number: erpItemNumber,
      })
      load()
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
    } finally {
      setSaving(false)
    }
  }

  return (
    <section className="entity-manager">
      <button type="button" onClick={onBack}>
        ← Back
      </button>
      <h2>Item Creation · {item.status}</h2>
      <table className="detail-table">
        <tbody>
          <tr>
            <th>Color</th>
            <td>{item.color}</td>
          </tr>
          <tr>
            <th>Size</th>
            <td>{item.size}</td>
          </tr>
          <tr>
            <th>ERP item number</th>
            <td>{item.erp_item_number ?? '—'}</td>
          </tr>
        </tbody>
      </table>

      {canComplete && (
        <form onSubmit={submit} className="entity-form action-form">
          <h4>Create item in ERP</h4>
          <label>
            <span>ERP item number</span>
            <input value={erpItemNumber} onChange={(e) => setErpItemNumber(e.target.value)} required />
          </label>
          <button type="submit" disabled={saving}>
            {saving ? 'Saving…' : 'Mark created'}
          </button>
        </form>
      )}
      {error && <p className="error">{error}</p>}
    </section>
  )
}
