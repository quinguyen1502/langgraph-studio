/** My chat accounts (TASK-0022): one slot per platform / Slack workspace; link -> one-time code by DM -> verify. */
import { useCallback, useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { RotateCw, Send, ShieldCheck } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { ErrorAlert } from '@/components/approvals/channel-parts'
import { api } from '@/lib/api'

export type Slot = { kind: string; team_id: string | null; team_name: string | null; available: boolean; external_id: string | null; verified: boolean; code_pending: boolean; code_expires: number | null }
export type Slots = { slots: Slot[] }

export function useSlots() {
  const [data, setData] = useState<Slots | null>(null); const [err, setErr] = useState('')
  const load = useCallback(() => api<Slots>('/api/approvals/identities').then(d => { setData(d); setErr('') }).catch(e => setErr(e.message)), [])
  useEffect(() => { load() }, [load])
  return { slots: data?.slots ?? null, setData, load, err }
}

export function IdentityRow({ slot, onChange }: { slot: Slot; onChange: (d: Slots) => void }) {
  const { t } = useTranslation(); const { kind } = slot; const team = slot.team_id ? { team_id: slot.team_id } : {}
  const idp = `id-${kind}${slot.team_id ? `-${slot.team_id}` : ''}`
  const [ext, setExt] = useState(slot.external_id || ''); const [code, setCode] = useState(''); const [err, setErr] = useState(''); const [busy, setBusy] = useState(false)
  useEffect(() => { setExt(slot.external_id || '') }, [slot.external_id])
  const call = async (path: string, init: Parameters<typeof api>[1]) => {
    setErr(''); setBusy(true)
    try { onChange(await api<Slots>(path, init)); return true } catch (e: any) { setErr(e.message); return false } finally { setBusy(false) }
  }
  const linkAndSend = async () => {
    if (await call('/api/approvals/identities', { method: 'PUT', json: { kind, external_id: ext.trim(), ...team } }) && ext.trim())
      await call(`/api/approvals/identities/${kind}/send-code`, { method: 'POST', json: team })
  }
  const changed = ext.trim() !== (slot.external_id || '')
  return <div className="space-y-2 rounded-lg border p-4" data-testid={idp}>
    <div className="flex flex-wrap items-center gap-2">
      <Label htmlFor={idp}>{t(`approvals.identity.${kind}`)}</Label>
      {slot.team_id && <Badge variant="outline">{slot.team_name || slot.team_id}</Badge>}
      {slot.external_id && (slot.verified ? <Badge id={`${idp}-verified`}><ShieldCheck />{t('approvals.verified')}</Badge> : <Badge variant="outline">{t('approvals.unverified')}</Badge>)}
      {!slot.available && <Badge variant="secondary">{t('approvals.noConnection')}</Badge>}
    </div>
    <div className="flex gap-2">
      <Input id={idp} className="font-mono" value={ext} placeholder={t(`approvals.identityPh.${kind}`)} onChange={e => setExt(e.target.value)} />
      <Button size="sm" variant={changed ? 'default' : 'outline'} id={`${idp}-link`} disabled={busy || !changed && (slot.verified || !ext.trim())}
        onClick={linkAndSend}><Send />{ext.trim() ? t('approvals.linkSend') : t('approvals.unlink')}</Button>
    </div>
    <p className="text-xs text-muted-foreground">{t(`approvals.identityHow.${kind}`)}</p>
    {slot.external_id && !slot.verified && !changed && <div className="space-y-1.5">
      <Label htmlFor={`${idp}-code`} className="text-xs">{slot.code_pending ? t('approvals.codeSent') : t('approvals.codeNeeded')}</Label>
      <div className="flex flex-wrap gap-2">
        <Input id={`${idp}-code`} className="w-36 font-mono tracking-widest" inputMode="numeric" maxLength={6} placeholder="123456" value={code} onChange={e => setCode(e.target.value.replace(/\D/g, ''))} />
        <Button size="sm" id={`${idp}-verify`} disabled={busy || code.length !== 6}
          onClick={async () => { if (await call(`/api/approvals/identities/${kind}/verify`, { method: 'POST', json: { code, ...team } })) setCode('') }}><ShieldCheck />{t('approvals.verify')}</Button>
        <Button size="sm" variant="ghost" id={`${idp}-resend`} disabled={busy || !slot.available} onClick={() => call(`/api/approvals/identities/${kind}/send-code`, { method: 'POST', json: team })}><RotateCw />{t('approvals.resend')}</Button>
      </div>
      {kind === 'telegram' && <p className="text-xs text-muted-foreground">{t('approvals.telegramStart')}</p>}
    </div>}
    {err && <ErrorAlert>{err}</ErrorAlert>}
  </div>
}

export const slotKey = (s: Slot) => `${s.kind}:${s.team_id || ''}`
