import { useEffect, useState, type FormEvent } from 'react'
import { apiGet, apiPost } from '../api'
import { useOptions } from '../useOptions'
import { hasAnyRole, useSession } from '../session'
import type {
  Factory,
  FactoryQuoteOption,
  Location,
  MarginRecommendation,
  PricingRequestDetail as PricingRequestDetailType,
  QuoteLine,
} from '../types'

export function PricingRequestDetailView({ id, onBack }: { id: string; onBack: () => void }) {
  const { user } = useSession()
  const [pr, setPr] = useState<PricingRequestDetailType | null>(null)
  const [error, setError] = useState<string | null>(null)
  const locationOptions = useOptions<Location>('/locations', (l) => l.name)

  const load = async () => {
    try {
      setPr(await apiGet<PricingRequestDetailType>(`/pricing-requests/${id}`))
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
    }
  }

  useEffect(() => {
    load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id])

  if (!pr) return <p>Loading…</p>

  const locationName = (locId: string) => locationOptions.find((o) => o.value === locId)?.label ?? locId
  const canClaim = pr.status === 'open' && hasAnyRole(user, ['costing'])
  const canAddLine = hasAnyRole(user, ['sales'])

  const claim = async () => {
    if (!user) return
    try {
      await apiPost(`/pricing-requests/${pr.id}/claim`, { actor_id: user.id })
      load()
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
    }
  }

  return (
    <section className="entity-manager">
      <button type="button" onClick={onBack}>
        ← Back to list
      </button>
      <h2>
        Pricing Request · {pr.source_type} · {pr.status}
      </h2>
      <table className="detail-table">
        <tbody>
          <tr>
            <th>Requested delivery date</th>
            <td>{pr.requested_delivery_date ?? '—'}</td>
          </tr>
          <tr>
            <th>Quote valid until</th>
            <td>{pr.requested_quote_validity_until ?? '—'}</td>
          </tr>
          <tr>
            <th>Assigned to costing</th>
            <td>{pr.assigned_costing_user_id ?? 'unclaimed'}</td>
          </tr>
        </tbody>
      </table>

      {canClaim && (
        <button type="button" onClick={claim}>
          Claim this pricing request
        </button>
      )}

      <h3>Lines</h3>
      {pr.lines.length === 0 ? (
        <p>None yet.</p>
      ) : (
        pr.lines.map((line) => (
          <QuoteLineCard
            key={line.id}
            line={line}
            pr={pr}
            locationName={locationName}
            onDone={load}
          />
        ))
      )}

      {canAddLine && <AddLineForm pricingRequestId={pr.id} locationOptions={locationOptions} onDone={load} />}
      {error && <p className="error">{error}</p>}
    </section>
  )
}

function QuoteLineCard({
  line,
  pr,
  locationName,
  onDone,
}: {
  line: QuoteLine
  pr: PricingRequestDetailType
  locationName: (id: string) => string
  onDone: () => void
}) {
  const { user } = useSession()
  const canPrice =
    line.status === 'requested' &&
    hasAnyRole(user, ['costing']) &&
    user?.id === pr.assigned_costing_user_id
  const canOverride = hasAnyRole(user, ['sales_director'])

  return (
    <div className="entity-form" style={{ flexDirection: 'column', alignItems: 'stretch' }}>
      <table className="detail-table">
        <tbody>
          <tr>
            <th>Variation</th>
            <td>
              {line.color} · {line.size} · qty {line.quantity}
            </td>
          </tr>
          <tr>
            <th>Production / delivery</th>
            <td>
              {locationName(line.production_location_id)} → {locationName(line.delivery_location_id)}
            </td>
          </tr>
          <tr>
            <th>Status</th>
            <td>{line.status}</td>
          </tr>
          {line.status === 'priced' && (
            <>
              <tr>
                <th>HS code</th>
                <td>{line.hs_code}</td>
              </tr>
              <tr>
                <th>Purchase price</th>
                <td>
                  {line.purchase_price} {line.purchase_currency}
                </td>
              </tr>
              <tr>
                <th>Box dims (W×L×H cm) × qty</th>
                <td>
                  {line.box_width_cm} × {line.box_length_cm} × {line.box_height_cm} × {line.box_qty}
                </td>
              </tr>
              <tr>
                <th>Volume (CBM)</th>
                <td>{line.volume_cbm?.toFixed(4)}</td>
              </tr>
              <tr>
                <th>Freight cost</th>
                <td>{line.freight_cost?.toFixed(2)}</td>
              </tr>
              <tr>
                <th>Duty cost</th>
                <td>{line.duty_cost?.toFixed(2)}</td>
              </tr>
              <tr>
                <th>Handling cost</th>
                <td>{line.handling_cost?.toFixed(2)}</td>
              </tr>
              <tr>
                <th>Landed cost</th>
                <td>{line.landed_cost?.toFixed(2)}</td>
              </tr>
              <tr>
                <th>Margin %</th>
                <td>{line.margin_pct}</td>
              </tr>
              <tr>
                <th>Sell price</th>
                <td>{line.sell_price?.toFixed(2)}</td>
              </tr>
            </>
          )}
        </tbody>
      </table>

      <QuoteOptionsSection pricingRequestId={pr.id} line={line} onDone={onDone} />

      {canPrice && <PriceLineForm pricingRequestId={pr.id} line={line} onDone={onDone} />}
      {canOverride && <OverrideLineForm pricingRequestId={pr.id} line={line} onDone={onDone} />}
    </div>
  )
}

function QuoteOptionsSection({
  pricingRequestId,
  line,
  onDone,
}: {
  pricingRequestId: string
  line: QuoteLine
  onDone: () => void
}) {
  const { user } = useSession()
  const [options, setOptions] = useState<FactoryQuoteOption[]>([])
  const factoryOptions = useOptions<Factory>('/factories', (f) => f.name)
  const [factoryId, setFactoryId] = useState('')
  const [quotedPrice, setQuotedPrice] = useState('')
  const [currency, setCurrency] = useState('EUR')
  const [notes, setNotes] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

  const canLog = hasAnyRole(user, ['costing'])

  const load = async () =>
    setOptions(
      await apiGet<FactoryQuoteOption[]>(`/pricing-requests/${pricingRequestId}/lines/${line.id}/quote-options`),
    )

  useEffect(() => {
    load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [line.id])

  const factoryName = (id: string) => factoryOptions.find((o) => o.value === id)?.label ?? id

  const addOption = async (e: FormEvent) => {
    e.preventDefault()
    if (!factoryId || !quotedPrice) return
    setSaving(true)
    setError(null)
    try {
      await apiPost(`/pricing-requests/${pricingRequestId}/lines/${line.id}/quote-options`, {
        factory_id: factoryId,
        quoted_price: Number(quotedPrice),
        currency,
        notes: notes || undefined,
      })
      setFactoryId('')
      setQuotedPrice('')
      setNotes('')
      load()
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
    } finally {
      setSaving(false)
    }
  }

  const selectOption = async (optionId: string) => {
    try {
      await apiPost(
        `/pricing-requests/${pricingRequestId}/lines/${line.id}/quote-options/${optionId}/select`,
        {},
      )
      load()
      onDone()
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
    }
  }

  return (
    <div>
      <h4>Factory quote options</h4>
      {options.length === 0 ? (
        <p>None logged yet.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Factory</th>
              <th>Quoted price</th>
              <th>Est. landed cost</th>
              <th>Notes</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {options.map((o) => (
              <tr key={o.id}>
                <td>{factoryName(o.factory_id)}</td>
                <td>
                  {o.quoted_price} {o.currency}
                </td>
                <td>{o.landed_cost != null ? o.landed_cost.toFixed(2) : '—'}</td>
                <td>{o.notes ?? '—'}</td>
                <td>
                  {o.is_selected ? (
                    'selected'
                  ) : (
                    <button type="button" onClick={() => selectOption(o.id)}>
                      Select
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      {canLog && (
        <form onSubmit={addOption} className="entity-form">
          <label>
            <span>Factory</span>
            <select value={factoryId} onChange={(e) => setFactoryId(e.target.value)} required>
              <option value="">-- select --</option>
              {factoryOptions.map((o) => (
                <option key={o.value} value={o.value}>
                  {o.label}
                </option>
              ))}
            </select>
          </label>
          <label>
            <span>Quoted price</span>
            <input type="number" step="0.01" value={quotedPrice} onChange={(e) => setQuotedPrice(e.target.value)} required />
          </label>
          <label>
            <span>Currency</span>
            <input value={currency} onChange={(e) => setCurrency(e.target.value)} required />
          </label>
          <label>
            <span>Notes</span>
            <input value={notes} onChange={(e) => setNotes(e.target.value)} />
          </label>
          <button type="submit" disabled={saving}>
            {saving ? 'Saving…' : 'Log option'}
          </button>
          {error && <p className="error">{error}</p>}
        </form>
      )}
    </div>
  )
}

function PriceLineForm({
  pricingRequestId,
  line,
  onDone,
}: {
  pricingRequestId: string
  line: QuoteLine
  onDone: () => void
}) {
  const { user } = useSession()
  const factoryOptions = useOptions<Factory>('/factories', (f) => f.name)
  const [factoryId, setFactoryId] = useState('')
  const [hsCode, setHsCode] = useState('')
  const [purchasePrice, setPurchasePrice] = useState('')
  const [purchaseCurrency, setPurchaseCurrency] = useState('EUR')
  const [boxWidth, setBoxWidth] = useState('')
  const [boxLength, setBoxLength] = useState('')
  const [boxHeight, setBoxHeight] = useState('')
  const [boxQty, setBoxQty] = useState('')
  const [marginPct, setMarginPct] = useState('')
  const [recommendation, setRecommendation] = useState<MarginRecommendation | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    apiGet<MarginRecommendation>(
      `/pricing-requests/${pricingRequestId}/lines/${line.id}/margin-recommendation`,
    ).then(setRecommendation)
  }, [pricingRequestId, line.id])

  const submit = async (e: FormEvent) => {
    e.preventDefault()
    if (!user) return
    setSaving(true)
    setError(null)
    try {
      await apiPost(`/pricing-requests/${pricingRequestId}/lines/${line.id}/price`, {
        actor_id: user.id,
        factory_id: factoryId,
        hs_code: hsCode,
        purchase_price: Number(purchasePrice),
        purchase_currency: purchaseCurrency,
        box_width_cm: Number(boxWidth),
        box_length_cm: Number(boxLength),
        box_height_cm: Number(boxHeight),
        box_qty: Number(boxQty),
        margin_pct: Number(marginPct),
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
      <h4>Price this line</h4>
      <label>
        <span>Factory</span>
        <select value={factoryId} onChange={(e) => setFactoryId(e.target.value)} required>
          <option value="">-- select --</option>
          {factoryOptions.map((o) => (
            <option key={o.value} value={o.value}>
              {o.label}
            </option>
          ))}
        </select>
      </label>
      <label>
        <span>HS code</span>
        <input value={hsCode} onChange={(e) => setHsCode(e.target.value)} required />
      </label>
      <label>
        <span>Purchase price</span>
        <input type="number" step="0.01" value={purchasePrice} onChange={(e) => setPurchasePrice(e.target.value)} required />
      </label>
      <label>
        <span>Purchase currency</span>
        <input value={purchaseCurrency} onChange={(e) => setPurchaseCurrency(e.target.value)} required />
      </label>
      <label>
        <span>Box width (cm)</span>
        <input type="number" step="0.01" value={boxWidth} onChange={(e) => setBoxWidth(e.target.value)} required />
      </label>
      <label>
        <span>Box length (cm)</span>
        <input type="number" step="0.01" value={boxLength} onChange={(e) => setBoxLength(e.target.value)} required />
      </label>
      <label>
        <span>Box height (cm)</span>
        <input type="number" step="0.01" value={boxHeight} onChange={(e) => setBoxHeight(e.target.value)} required />
      </label>
      <label>
        <span>Box quantity</span>
        <input type="number" value={boxQty} onChange={(e) => setBoxQty(e.target.value)} required />
      </label>
      <label>
        <span>Margin %{recommendation?.recommended_margin_pct != null && ` (recommended ${recommendation.recommended_margin_pct.toFixed(1)}%, based on ${recommendation.based_on_count} won quotes)`}</span>
        <input type="number" step="0.01" value={marginPct} onChange={(e) => setMarginPct(e.target.value)} required />
      </label>
      <button type="submit" disabled={saving}>
        {saving ? 'Saving…' : 'Save price'}
      </button>
      {error && <p className="error">{error}</p>}
    </form>
  )
}

function OverrideLineForm({
  pricingRequestId,
  line,
  onDone,
}: {
  pricingRequestId: string
  line: QuoteLine
  onDone: () => void
}) {
  const { user } = useSession()
  const [marginPct, setMarginPct] = useState(line.margin_pct != null ? String(line.margin_pct) : '')
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

  const submit = async (e: FormEvent) => {
    e.preventDefault()
    if (!user || !marginPct) return
    setSaving(true)
    setError(null)
    try {
      await apiPost(`/pricing-requests/${pricingRequestId}/lines/${line.id}/override`, {
        actor_id: user.id,
        margin_pct: Number(marginPct),
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
      <h4>Override (Sales Director)</h4>
      <label>
        <span>Margin %</span>
        <input type="number" step="0.01" value={marginPct} onChange={(e) => setMarginPct(e.target.value)} required />
      </label>
      <button type="submit" disabled={saving}>
        {saving ? 'Saving…' : 'Override margin'}
      </button>
      {error && <p className="error">{error}</p>}
    </form>
  )
}

function AddLineForm({
  pricingRequestId,
  locationOptions,
  onDone,
}: {
  pricingRequestId: string
  locationOptions: { value: string; label: string }[]
  onDone: () => void
}) {
  const { user } = useSession()
  const [color, setColor] = useState('')
  const [size, setSize] = useState('')
  const [quantity, setQuantity] = useState('')
  const [productionLocationId, setProductionLocationId] = useState('')
  const [deliveryLocationId, setDeliveryLocationId] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

  const submit = async (e: FormEvent) => {
    e.preventDefault()
    if (!user) return
    setSaving(true)
    setError(null)
    try {
      await apiPost(`/pricing-requests/${pricingRequestId}/lines`, {
        actor_id: user.id,
        color,
        size,
        quantity: Number(quantity),
        production_location_id: productionLocationId,
        delivery_location_id: deliveryLocationId,
      })
      setColor('')
      setSize('')
      setQuantity('')
      setProductionLocationId('')
      setDeliveryLocationId('')
      onDone()
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
    } finally {
      setSaving(false)
    }
  }

  return (
    <form onSubmit={submit} className="entity-form">
      <h4>Add another variation</h4>
      <label>
        <span>Color</span>
        <input value={color} onChange={(e) => setColor(e.target.value)} required />
      </label>
      <label>
        <span>Size</span>
        <input value={size} onChange={(e) => setSize(e.target.value)} required />
      </label>
      <label>
        <span>Quantity</span>
        <input type="number" value={quantity} onChange={(e) => setQuantity(e.target.value)} required />
      </label>
      <label>
        <span>Production location</span>
        <select value={productionLocationId} onChange={(e) => setProductionLocationId(e.target.value)} required>
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
        <select value={deliveryLocationId} onChange={(e) => setDeliveryLocationId(e.target.value)} required>
          <option value="">-- select --</option>
          {locationOptions.map((o) => (
            <option key={o.value} value={o.value}>
              {o.label}
            </option>
          ))}
        </select>
      </label>
      <button type="submit" disabled={saving}>
        {saving ? 'Saving…' : 'Add line'}
      </button>
      {error && <p className="error">{error}</p>}
    </form>
  )
}
