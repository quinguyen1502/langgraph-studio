import i18n, { eventErrors, type ApiErrorBody } from '@/lib/i18n'
// Turns the run event stream into one span per node execution (LangSmith/Langfuse-style trace).
export type RunEvent = { type: string; node?: string; label?: string; node_type?: string; iteration?: number; duration_ms?: number
  input?: any; delta?: any; state?: any; errors?: string[]; error?: ApiErrorBody; ts?: number; tokens?: number; usage?: { total_tokens?: number }; run_id?: string; status?: string; reason?: string }
export type Span = { key: string; node: string; label: string; type: string; iter: number; status: 'running' | 'done' | 'error' | 'cancelled'
  start: number; end?: number; duration?: number; input?: any; output?: any; error?: string; tokens?: number; events: RunEvent[] }
export type Trace = { spans: Span[]; status: 'idle' | 'running' | 'ok' | 'error' | 'cancelled' | 'timeout'; start?: number; end?: number; total?: number
  tokens?: number; errors: string[]; final?: any }

export function buildTrace(events: RunEvent[], meta: (id: string) => { label?: string; type?: string } = () => ({})): Trace {
  const spans: Span[] = []; const counts: Record<string, number> = {}; const errors: string[] = []
  const st = { v: (events.length ? 'running' : 'idle') as Trace['status'] }; let final: any
  const open = (n: string) => [...spans].reverse().find(s => s.node === n && s.status === 'running')
  const t = (e: RunEvent, i: number) => e.ts ?? i / 1000
  events.forEach((e, i) => {
    const n = e.node
    if (e.type === 'node_started' && n) {
      const it = (counts[n] = (counts[n] || 0) + 1); const m = meta(n)
      spans.push({ key: `${n}#${it}`, node: n, label: e.label || m.label || n, type: e.node_type || m.type || 'code', iter: it, status: 'running', start: t(e, i), events: [e] })
    } else if (e.type === 'node_finished' && n) {
      let s = open(n)
      if (!s) { const it = (counts[n] = (counts[n] || 0) + 1); s = { key: `${n}#${it}`, node: n, label: e.label || meta(n).label || n, type: e.node_type || meta(n).type || 'code', iter: it, status: 'running', start: t(e, i) - (e.duration_ms || 0) / 1000, events: [] }; spans.push(s) }
      Object.assign(s, { status: 'done', end: t(e, i), duration: e.duration_ms, input: e.input, output: e.delta, tokens: e.tokens ?? e.usage?.total_tokens })
      s.events.push(e)
    } else if (e.type === 'error') {
      st.v = e.status === 'timeout' ? 'timeout' : 'error'; const msg = eventErrors(e).join('; ') || i18n.t('trace.error'); errors.push(msg)
      const s = (n ? open(n) ?? [...spans].reverse().find(x => x.node === n) : undefined) ?? (e.status === 'timeout' ? undefined : [...spans].reverse().find(x => x.status === 'running'))
      if (s) { Object.assign(s, { status: 'error', end: t(e, i), duration: e.duration_ms ?? s.duration, error: msg, input: e.input ?? s.input }); s.events.push(e) }
    } else if (e.type === 'run_cancelled') { st.v = 'cancelled'
    } else if (e.type === 'run_finished') { if (st.v !== 'error') st.v = 'ok'; final = e.state }
  })
  // Speculative "started" rows (predicted next nodes) that never ran are dropped once the run ends.
  const status = st.v; const done = status !== 'running' && status !== 'idle'
  // Rows still running when a run is cancelled / times out are shown as cancelled; speculative
  // "started" rows (predicted next nodes) are dropped once a run finishes normally.
  if (status === 'cancelled' || status === 'timeout') spans.forEach(s => { if (s.status === 'running') s.status = 'cancelled' })
  const kept = done ? spans.filter(s => s.status !== 'running') : spans
  const stamped = events.filter(e => e.ts != null)
  const start = stamped.length ? stamped[0].ts : kept[0]?.start
  const end = stamped.length ? stamped[stamped.length - 1].ts : kept[kept.length - 1]?.end
  const tokens = kept.reduce((a, s) => a + (s.tokens || 0), 0)
  return { spans: kept, status, start, end, total: start != null && end != null ? (end - start) * 1000 : undefined, tokens: tokens || undefined, errors, final }
}

export type DiffRow = { key: string; kind: 'added' | 'changed' | 'removed' | 'same'; before?: any; after?: any }
export function stateDiff(before: any = {}, output: any = {}): DiffRow[] {
  const b = before && typeof before === 'object' && !before._truncated ? before : {}
  const o = output && typeof output === 'object' && !output._truncated ? output : {}
  const after = { ...b, ...o }; const keys = [...new Set([...Object.keys(b), ...Object.keys(after)])]
  const eq = (x: any, y: any) => JSON.stringify(x) === JSON.stringify(y)
  return keys.map(k => !(k in b) ? { key: k, kind: 'added' as const, after: after[k] }
    : !(k in after) ? { key: k, kind: 'removed' as const, before: b[k] }
    : eq(b[k], after[k]) ? { key: k, kind: 'same' as const, before: b[k], after: after[k] }
    : { key: k, kind: 'changed' as const, before: b[k], after: after[k] })
    .sort((x, y) => (x.kind === 'same' ? 1 : 0) - (y.kind === 'same' ? 1 : 0))
}
export const fmtMs = (ms?: number) => ms == null ? '—' : ms < 1 ? `${ms.toFixed(2)} ms` : ms < 1000 ? `${Math.round(ms)} ms` : `${(ms / 1000).toFixed(2)} s`
