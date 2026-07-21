import { createContext, useContext } from 'react'
import type { Role, User } from './types'

const STORAGE_KEY = 'claudie.currentUserId'

export interface SessionContextValue {
  user: User | null
  setUser: (user: User | null) => void
}

export const SessionContext = createContext<SessionContextValue | null>(null)

export function useSession(): SessionContextValue {
  const ctx = useContext(SessionContext)
  if (!ctx) throw new Error('useSession must be used within a SessionContext provider')
  return ctx
}

export function hasAnyRole(user: User | null, roles: Role[]): boolean {
  if (!user) return false
  return roles.some((r) => user.roles.includes(r))
}

export function saveCurrentUserId(id: string) {
  localStorage.setItem(STORAGE_KEY, id)
}

export function loadCurrentUserId(): string | null {
  return localStorage.getItem(STORAGE_KEY)
}

export function clearCurrentUserId() {
  localStorage.removeItem(STORAGE_KEY)
}
