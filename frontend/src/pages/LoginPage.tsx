import { useEffect, useState } from 'react'
import { apiGet } from '../api'
import type { User } from '../types'
import { saveCurrentUserId } from '../session'

interface LoginPageProps {
  onPick: (user: User) => void
}

export function LoginPage({ onPick }: LoginPageProps) {
  const [users, setUsers] = useState<User[]>([])
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    apiGet<User[]>('/users')
      .then(setUsers)
      .catch((err) => setError(err instanceof Error ? err.message : String(err)))
      .finally(() => setLoading(false))
  }, [])

  const filtered = users.filter(
    (u) =>
      u.name.toLowerCase().includes(query.toLowerCase()) ||
      u.email.toLowerCase().includes(query.toLowerCase()),
  )

  const pick = (user: User) => {
    saveCurrentUserId(user.id)
    onPick(user)
  }

  return (
    <div className="login-page">
      <div className="login-box">
        <h1>Claudie</h1>
        <p className="login-subtitle">
          No login system yet - pick which existing user you're acting as.
        </p>
        <input
          type="text"
          placeholder="Search by name or email…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          autoFocus
        />
        {error && <p className="error">{error}</p>}
        {loading ? (
          <p>Loading users…</p>
        ) : (
          <ul className="login-user-list">
            {filtered.map((u) => (
              <li key={u.id}>
                <button type="button" onClick={() => pick(u)}>
                  <strong>{u.name}</strong>
                  <span>{u.email}</span>
                  <span className="login-roles">{u.roles.join(', ') || 'no roles'}</span>
                </button>
              </li>
            ))}
            {filtered.length === 0 && !loading && <li className="login-empty">No users match.</li>}
          </ul>
        )}
      </div>
    </div>
  )
}
