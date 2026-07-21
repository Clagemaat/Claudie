import { useEffect, useState } from 'react'
import { apiGet } from './api'
import type { FieldOption } from './components/EntityManager'
import type { WithId } from './types'

/** Fetches a list endpoint and turns it into dropdown options via labelOf. */
export function useOptions<T extends WithId>(path: string, labelOf: (row: T) => string): FieldOption[] {
  const [options, setOptions] = useState<FieldOption[]>([])

  useEffect(() => {
    let cancelled = false
    apiGet<T[]>(path).then((rows) => {
      if (!cancelled) setOptions(rows.map((r) => ({ value: r.id, label: labelOf(r) })))
    })
    return () => {
      cancelled = true
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [path])

  return options
}
