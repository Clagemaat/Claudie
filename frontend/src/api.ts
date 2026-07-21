// Dev: the Vite dev server proxies '/api' to the backend on :8000 (see
// vite.config.ts). Prod: frontend and backend are served from the same
// origin by the same process (see Dockerfile), so requests are unprefixed.
const BASE = import.meta.env.DEV ? '/api' : ''

async function extractError(res: Response): Promise<string> {
  try {
    const data = await res.json()
    if (typeof data.detail === 'string') return data.detail
    if (Array.isArray(data.detail)) {
      return data.detail.map((d: { loc?: string[]; msg: string }) => `${d.loc?.at(-1)}: ${d.msg}`).join(', ')
    }
    return JSON.stringify(data)
  } catch {
    return res.statusText
  }
}

export async function apiGet<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`)
  if (!res.ok) throw new Error(await extractError(res))
  return res.json() as Promise<T>
}

export async function apiPost<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) throw new Error(await extractError(res))
  return res.json() as Promise<T>
}

export async function apiUpload<T>(path: string, form: FormData): Promise<T> {
  const res = await fetch(`${BASE}${path}`, { method: 'POST', body: form })
  if (!res.ok) throw new Error(await extractError(res))
  return res.json() as Promise<T>
}

/** Uploads a file via the generic /uploads endpoint and returns its URL. */
export async function uploadFile(file: File): Promise<string> {
  const form = new FormData()
  form.append('file', file)
  const { url } = await apiUpload<{ url: string }>('/uploads', form)
  return url
}
