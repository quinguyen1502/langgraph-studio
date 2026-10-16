export const getToken = () => localStorage.getItem('token')
export const getUser = (): { id: string; email: string } | null => JSON.parse(localStorage.getItem('user') || 'null')
export function setSession(token: string, user: any) { localStorage.setItem('token', token); localStorage.setItem('user', JSON.stringify(user)) }
function clearSession() { localStorage.removeItem('token'); localStorage.removeItem('user') }
export function logout() { clearSession(); location.href = '/login' }

/** Seconds-since-epoch expiry from the JWT payload (no signature check; server is authoritative). */
export function tokenExp(t = getToken()): number | null {
  try { return JSON.parse(atob(t!.split('.')[1].replace(/-/g, '+').replace(/_/g, '/'))).exp ?? null } catch { return null }
}
export const tokenValid = (t = getToken()) => { const e = tokenExp(t); return !!t && !!e && e * 1000 > Date.now() }

export const loginUrl = (expired: boolean, next = location.pathname + location.search) =>
  `/login?${expired ? 'expired=1&' : ''}next=${encodeURIComponent(next)}`
/** Clear session and send the user to /login with an "expired" notice, coming back here afterwards. */
export function sessionExpired() {
  if (location.pathname === '/login') return
  clearSession(); location.href = loginUrl(true)
}
/** Auto-logout exactly when the token expires (call once at app start). */
let timer: number | undefined
export function scheduleExpiry() {
  clearTimeout(timer); const e = tokenExp(); if (!e) return
  const ms = e * 1000 - Date.now()
  // setTimeout overflows above 2^31-1 ms (~24.8 days) and would fire immediately; re-check later instead.
  timer = ms > 2 ** 31 - 1 ? window.setTimeout(scheduleExpiry, 2 ** 31 - 1) : window.setTimeout(sessionExpired, Math.max(0, ms))
}

export class ApiError extends Error { status: number; constructor(msg: string, status: number) { super(msg); this.status = status } }

export async function api<T = any>(path: string, opts: RequestInit & { json?: any } = {}): Promise<T> {
  const headers: Record<string, string> = { ...(opts.headers as any) }
  const t = getToken(); if (t) headers.Authorization = `Bearer ${t}`
  if (opts.json !== undefined) { headers['Content-Type'] = 'application/json'; opts.body = JSON.stringify(opts.json) }
  let r: Response
  try { r = await fetch(path, { ...opts, headers }) } catch { throw new ApiError('Không kết nối được máy chủ. Kiểm tra mạng rồi thử lại.', 0) }
  if (r.status === 401 && !path.startsWith('/api/auth')) { sessionExpired(); throw new ApiError('Phiên đăng nhập đã hết hạn', 401) }
  const data = await r.json().catch(() => ({}))
  if (!r.ok) throw new ApiError(typeof data.detail === 'string' ? data.detail : r.status >= 500 ? 'Lỗi máy chủ, thử lại sau' : `HTTP ${r.status}`, r.status)
  return data
}
export const wsUrl = (p: string) => `${location.protocol === 'https:' ? 'wss' : 'ws'}://${location.host}${p}?token=${encodeURIComponent(getToken() || '')}`
