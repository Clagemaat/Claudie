import { useState } from 'react'
import { UsersPage } from './UsersPage'
import { LocationsPage } from './LocationsPage'
import { ProductTypesPage } from './ProductTypesPage'
import { FactoriesPage } from './FactoriesPage'
import { ExchangeRatesPage } from './ExchangeRatesPage'
import { FreightRatesPage } from './FreightRatesPage'
import { DutyRatesPage } from './DutyRatesPage'
import { HandlingCostsPage } from './HandlingCostsPage'
import { SLADefinitionsPage } from './SLADefinitionsPage'
import { EscalationRulesPage } from './EscalationRulesPage'

const SECTIONS = [
  { key: 'users', label: 'Users', Component: UsersPage },
  { key: 'locations', label: 'Locations', Component: LocationsPage },
  { key: 'product-types', label: 'Product Types', Component: ProductTypesPage },
  { key: 'factories', label: 'Factories', Component: FactoriesPage },
  { key: 'exchange-rates', label: 'Exchange Rates', Component: ExchangeRatesPage },
  { key: 'freight-rates', label: 'Freight Rates', Component: FreightRatesPage },
  { key: 'duty-rates', label: 'Duty Rates', Component: DutyRatesPage },
  { key: 'handling-costs', label: 'Handling Costs', Component: HandlingCostsPage },
  { key: 'sla-definitions', label: 'SLA Definitions', Component: SLADefinitionsPage },
  { key: 'escalation-rules', label: 'Escalation Rules', Component: EscalationRulesPage },
] as const

export function AdminPage() {
  const [active, setActive] = useState<(typeof SECTIONS)[number]['key']>('users')
  const Active = SECTIONS.find((s) => s.key === active)!.Component

  return (
    <div className="admin-layout">
      <nav className="admin-subnav">
        <ul>
          {SECTIONS.map((s) => (
            <li key={s.key}>
              <button
                type="button"
                className={s.key === active ? 'active' : ''}
                onClick={() => setActive(s.key)}
              >
                {s.label}
              </button>
            </li>
          ))}
        </ul>
      </nav>
      <div className="admin-content">
        <Active />
      </div>
    </div>
  )
}
