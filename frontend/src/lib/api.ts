export const getToken = () => localStorage.getItem('token')
export const getUser = (): { id: string; email: string } | null => JSON.parse(localStorage.getItem('user') || 'null')
export function setSession(token: string, user: any) { localStorage.setItem('token', token); localStorage.setItem('user', JSON.stringify(user)) }
export function logout() { localStorage.removeItem('token'); localStorage.removeItem('user'); location.href = '/login' }

export async function api<T = any>(path: string, opts: RequestInit & { json?: any } = {}): Promise<T> {
  const headers: Record<string, string> = { ...(opts.headers as any) }
  const t = getToken(); if (t) headers.Authorization = `Bearer ${t}`
  if (opts.json !== undefined) { headers['Content-Type'] = 'application/json'; opts.body = JSON.stringify(opts.json) }
  const r = await fetch(path, { ...opts, headers })
  if (r.status === 401 && !path.startsWith('/api/auth')) { logout(); throw new Error('Unauthorized') }
  const data = await r.json().catch(() => ({}))
  if (!r.ok) throw new Error(data.detail || `HTTP ${r.status}`)
  return data
}
export const wsUrl = (p: string) => `${location.protocol === 'https:' ? 'wss' : 'ws'}://${location.host}${p}?token=${encodeURIComponent(getToken() || '')}`
