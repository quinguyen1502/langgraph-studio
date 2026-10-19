/** Tool node Code mode (TASK-0055): what the server can run, read once from GET /api/meta/runtime. */
import { useEffect, useState } from 'react'
import { api } from '@/lib/api'

export type CodeRuntime = {
  code_runtime: 'docker' | 'subprocess' | 'off'; available: boolean; problem: string | null; image: string; packages: string[]; starter: string
  limits: { memory: string; cpus: string; pids: number; seconds: number; source_kb: number }
}
export type CodeTestResult = { ok: boolean; value?: unknown; stdout?: string; traceback?: string; runtime?: string; duration_ms?: number
  error?: { code: string; message: string; details?: Record<string, unknown> } }

let cached: Promise<CodeRuntime> | null = null
export function loadCodeRuntime(): Promise<CodeRuntime> {
  cached ??= api<CodeRuntime>('/api/meta/runtime').catch(e => { cached = null; throw e })
  return cached
}

export function useCodeRuntime(): CodeRuntime | null {
  const [rt, setRt] = useState<CodeRuntime | null>(null)
  useEffect(() => { let live = true; loadCodeRuntime().then(r => { if (live) setRt(r) }).catch(() => {}); return () => { live = false } }, [])
  return rt
}
