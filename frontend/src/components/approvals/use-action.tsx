import { useState } from 'react'
import { Check } from 'lucide-react'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { ErrorAlert } from './error-alert'

/** Run an API call and show its error or a success note right where the button is. */
export function useAction(onDone: () => void = () => {}) {
  const [err, setErr] = useState(''); const [note, setNote] = useState(''); const [busy, setBusy] = useState(false)
  const run = async (fn: () => Promise<unknown>, ok: string | ((r: any) => string)) => {
    setErr(''); setNote(''); setBusy(true)
    try { const r = await fn(); setNote(typeof ok === 'function' ? ok(r) : ok); onDone(); return true }
    catch (e: any) { setErr(e.message); return false } finally { setBusy(false) }
  }
  const alerts = <>{err && <ErrorAlert>{err}</ErrorAlert>}
    {note && <Alert><Check /><AlertDescription>{note}</AlertDescription></Alert>}</>
  return { run, alerts, busy }
}
