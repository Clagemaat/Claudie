import { useEffect, useState } from 'react'
import { apiGet } from './api'
import { LoginPage } from './pages/LoginPage'
import { MyTasksPage } from './pages/MyTasksPage'
import { ProjectsPage } from './pages/ProjectsPage'
import { DesignRequestsPage } from './pages/DesignRequestsPage'
import { PricingRequestsPage } from './pages/PricingRequestsPage'
import { AdminPage } from './pages/AdminPage'
import { SessionContext, clearCurrentUserId, hasAnyRole, loadCurrentUserId } from './session'
import type { Role, User } from './types'

type SectionKey = 'my-tasks' | 'projects' | 'design-requests' | 'pricing-requests' | 'admin'

const NAV: { key: SectionKey; label: string; roles: Role[] | null }[] = [
  { key: 'my-tasks', label: 'My Tasks', roles: null },
  { key: 'projects', label: 'Projects', roles: ['sales'] },
  {
    key: 'design-requests',
    label: 'Design Requests',
    roles: ['sales', 'traffic_manager', 'lead_designer', 'dtp_designer'],
  },
  {
    key: 'pricing-requests',
    label: 'Pricing Requests',
    roles: ['sales', 'costing', 'sales_director'],
  },
  { key: 'admin', label: 'Admin', roles: ['admin'] },
]

function App() {
  const [user, setUser] = useState<User | null>(null)
  const [checkingSession, setCheckingSession] = useState(true)
  const [active, setActive] = useState<SectionKey>('my-tasks')
  const [focusDesignRequestId, setFocusDesignRequestId] = useState<string | null>(null)
  const [focusPricingRequestId, setFocusPricingRequestId] = useState<string | null>(null)

  useEffect(() => {
    const id = loadCurrentUserId()
    if (!id) {
      setCheckingSession(false)
      return
    }
    apiGet<User>(`/users/${id}`)
      .then(setUser)
      .catch(() => clearCurrentUserId())
      .finally(() => setCheckingSession(false))
  }, [])

  if (checkingSession) return null

  if (!user) {
    return <LoginPage onPick={setUser} />
  }

  const visibleNav = NAV.filter((n) => n.roles === null || hasAnyRole(user, n.roles))

  const openDesignRequest = (id: string) => {
    setFocusDesignRequestId(id)
    setActive('design-requests')
  }

  const openPricingRequest = (id: string) => {
    setFocusPricingRequestId(id)
    setActive('pricing-requests')
  }

  const signOut = () => {
    clearCurrentUserId()
    setUser(null)
  }

  return (
    <SessionContext.Provider value={{ user, setUser }}>
      <div className="app">
        <nav className="sidebar">
          <h1>Claudie</h1>
          <div className="signed-in-as">
            <strong>{user.name}</strong>
            <span>{user.roles.join(', ') || 'no roles'}</span>
            <button type="button" onClick={signOut}>
              Switch user
            </button>
          </div>
          <ul>
            {visibleNav.map((s) => (
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
          {active === 'my-tasks' && (
            <MyTasksPage onOpenDesignRequest={openDesignRequest} onOpenPricingRequest={openPricingRequest} />
          )}
          {active === 'projects' && <ProjectsPage />}
          {active === 'design-requests' && (
            <DesignRequestsPage
              focusId={focusDesignRequestId}
              onFocusHandled={() => setFocusDesignRequestId(null)}
            />
          )}
          {active === 'pricing-requests' && (
            <PricingRequestsPage
              focusId={focusPricingRequestId}
              onFocusHandled={() => setFocusPricingRequestId(null)}
            />
          )}
          {active === 'admin' && <AdminPage />}
        </main>
      </div>
    </SessionContext.Provider>
  )
}

export default App
