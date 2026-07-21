import { useState } from 'react'
import { UsersPage } from './pages/UsersPage'
import { CustomersPage } from './pages/CustomersPage'
import { LocationsPage } from './pages/LocationsPage'
import { ProductTypesPage } from './pages/ProductTypesPage'
import { FactoriesPage } from './pages/FactoriesPage'
import { ExchangeRatesPage } from './pages/ExchangeRatesPage'
import { FreightRatesPage } from './pages/FreightRatesPage'
import { DutyRatesPage } from './pages/DutyRatesPage'
import { HandlingCostsPage } from './pages/HandlingCostsPage'
import { SLADefinitionsPage } from './pages/SLADefinitionsPage'
import { EscalationRulesPage } from './pages/EscalationRulesPage'

const SECTIONS = [
  { key: 'users', label: 'Users', Component: UsersPage },
  { key: 'customers', label: 'Customers & Retailers', Component: CustomersPage },
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

function App() {
  const [active, setActive] = useState<(typeof SECTIONS)[number]['key']>('users')
  const Active = SECTIONS.find((s) => s.key === active)!.Component

  return (
    <div className="app">
      <nav className="sidebar">
        <h1>Claudie Admin</h1>
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
      <main className="content">
        <Active />
      </main>
    </div>
  )
}

export default App
