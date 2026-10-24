import { useEffect, useState } from 'react'
import { api } from '@/lib/api'

/** The public demo (STUDIO_DEMO_MODE): the shared read-only visitor account the sign-in page offers. */
export type DemoAccount = { email: string; password: string }
export type AuthOptions = { demo: boolean; reset: 'email' | 'admin'; demo_mode?: DemoAccount }

let cached: Promise<AuthOptions> | null = null
/** /api/auth/options, fetched once per page load (it never changes while the server runs). */
export function authOptions(): Promise<AuthOptions> {
  cached ??= api<AuthOptions>('/api/auth/options').catch(e => { cached = null; throw e })
  return cached
}

/** The demo visitor account when the server runs in demo mode, else null. */
export function useDemoMode(): DemoAccount | null {
  const [demo, setDemo] = useState<DemoAccount | null>(null)
  useEffect(() => { authOptions().then(o => setDemo(o.demo_mode ?? null)).catch(() => {}) }, [])
  return demo
}
