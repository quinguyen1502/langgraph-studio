import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { AlertCircle, Building2, Check, Copy, KeyRound, Plus, RotateCw, Save, Send, ShieldCheck, Trash2, User, Webhook } from 'lucide-react'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import type { Channel, ChannelKind, Channels } from '@/lib/approvals'
import { api } from '@/lib/api'
import i18n, { errorText } from '@/lib/i18n'

type Audit = { id: string; at: number; kind: string; action: string; code: string | null; run_id: string | null; workflow_name: string | null; actor: string | null; external_id: string | null }

const ACTION_VARIANT: Record<string, 'default' | 'secondary' | 'destructive' | 'outline'> = { approved: 'default', rejected: 'destructive', denied: 'outline', send_failed: 'destructive' }

function useAction(onDone: () => void) {
  const [err, setErr] = useState(''); const [note, setNote] = useState('')
  const run = async (fn: () => Promise<unknown>, ok: string) => { setErr(''); setNote(''); try { await fn(); setNote(ok); onDone(); return true } catch (e: any) { setErr(e.message); return false } }
  const alerts = <>{err && <Alert variant="destructive"><AlertCircle /><AlertDescription>{err}</AlertDescription></Alert>}
    {note && <Alert><Check /><AlertDescription>{note}</AlertDescription></Alert>}</>
  return { run, alerts }
}

function SecretFields({ k, vals, setVals, idp, placeholder }: { k: ChannelKind; vals: Record<string, string>; setVals: (f: (v: Record<string, string>) => Record<string, string>) => void; idp: string; placeholder?: string }) {
  const { t } = useTranslation()
  return <div className="grid gap-3 sm:grid-cols-2">
    {k.fields.map(f => <div key={f} className="space-y-1.5">
      <Label htmlFor={`${idp}-${f}`}>{t(`approvals.field.${f}`)}{k.optional.includes(f) && <span className="text-muted-foreground"> · {t('approvals.optional')}</span>}</Label>
      <Input id={`${idp}-${f}`} type="password" autoComplete="off" value={vals[f] || ''} placeholder={placeholder}
        onChange={e => setVals(v => ({ ...v, [f]: e.target.value }))} /></div>)}
  </div>
}

function CopyField({ id, label, value }: { id: string; label: string; value: string }) {
  const { t } = useTranslation(); const [copied, setCopied] = useState(false)
  return <div className="space-y-1.5"><Label htmlFor={id}>{label}</Label>
    <div className="flex gap-2"><Input readOnly value={value} className="font-mono text-xs" id={id} />
      <Button variant="outline" size="icon" aria-label={t('approvals.copy')} onClick={() => { navigator.clipboard?.writeText(value); setCopied(true); setTimeout(() => setCopied(false), 1500) }}>{copied ? <Check /> : <Copy />}</Button></div></div>
}

/** One connection: label, scope, callback URL; its owner (or an admin for org ones) can replace secrets, register, remove. */
function ChannelCard({ c, k, publicUrl, onChange }: { c: Channel; k: ChannelKind; publicUrl: string | null; onChange: () => void }) {
  const { t } = useTranslation(); const [vals, setVals] = useState<Record<string, string>>({}); const [edit, setEdit] = useState(false)
  const { run, alerts } = useAction(() => { setVals({}); onChange() })
  const url = c.callback_url || location.origin + c.callback_path
  return <div className="space-y-3 rounded-lg border p-4" data-testid={`channel-${c.kind}-${c.scope}`} data-channel-id={c.id}>
    <div className="flex flex-wrap items-center gap-2">
      <span className="font-medium">{t(`approvals.kind.${c.kind}`)}</span>
      {c.name && <span className="text-sm text-muted-foreground">{c.name}</span>}
      <Badge variant={c.scope === 'org' ? 'default' : 'secondary'}>{c.scope === 'org' ? <Building2 /> : <User />}{t(`approvals.scope.${c.scope}`)}</Badge>
      <Badge variant="outline" className="font-mono">{c.hint}</Badge>
    </div>
    <CopyField id={`ch-${c.id}-url`} label={t('approvals.callbackUrl')} value={url} />
    {!publicUrl && <p className="text-xs text-muted-foreground">{t('approvals.publicUrlMissing')}</p>}
    {!c.editable && <p className="text-xs text-muted-foreground">{t('approvals.orgReadOnly')}</p>}
    {edit && <SecretFields k={k} vals={vals} setVals={setVals} idp={`ch-${c.id}`} placeholder={t('approvals.keepSecret')} />}
    {alerts}
    {c.editable && <div className="flex flex-wrap justify-end gap-2">
      <Button variant="ghost" size="sm" onClick={() => run(() => api(`/api/approvals/channels/${c.id}`, { method: 'DELETE' }), t('approvals.removed'))}><Trash2 />{t('approvals.remove')}</Button>
      {c.kind === 'telegram' && <Button variant="outline" size="sm" id={`ch-${c.id}-register`}
        onClick={() => run(() => api(`/api/approvals/channels/${c.id}/register-webhook`, { method: 'POST' }), t('approvals.registered'))}><Webhook />{t('approvals.register')}</Button>}
      {edit ? <Button size="sm" id={`ch-${c.id}-save`} disabled={!k.fields.some(f => !k.optional.includes(f) && vals[f]?.trim())}
        onClick={async () => { if (await run(() => api(`/api/approvals/channels/${c.id}`, { method: 'PUT', json: vals }), t('approvals.saved'))) setEdit(false) }}><Save />{t('approvals.save')}</Button>
        : <Button variant="outline" size="sm" id={`ch-${c.id}-edit`} onClick={() => setEdit(true)}><KeyRound />{t('approvals.replaceSecrets')}</Button>}
    </div>}
  </div>
}

/** New connection: platform, scope (org only for admins), optional name, secrets. */
function AddChannel({ data, onChange }: { data: Channels; onChange: () => void }) {
  const { t } = useTranslation()
  const [kind, setKind] = useState(data.kinds[0]?.kind || 'slack'); const [scope, setScope] = useState<'user' | 'org'>('user')
  const [name, setName] = useState(''); const [vals, setVals] = useState<Record<string, string>>({})
  const { run, alerts } = useAction(() => { setVals({}); setName(''); onChange() })
  const k = data.kinds.find(x => x.kind === kind)
  if (!k) return null
  return <div className="space-y-3 rounded-lg border border-dashed p-4" id="add-channel">
    <div className="flex items-center gap-2 font-medium"><Plus className="size-4" />{t('approvals.add')}</div>
    <div className="grid gap-3 sm:grid-cols-3">
      <div className="space-y-1.5"><Label htmlFor="add-kind">{t('approvals.platform')}</Label>
        <Select value={kind} onValueChange={v => { setKind(v); setVals({}) }}><SelectTrigger className="w-full" id="add-kind"><SelectValue /></SelectTrigger>
          <SelectContent>{data.kinds.map(x => <SelectItem key={x.kind} value={x.kind}>{t(`approvals.kind.${x.kind}`)}</SelectItem>)}</SelectContent></Select></div>
      <div className="space-y-1.5"><Label htmlFor="add-scope">{t('approvals.scopeLabel')}</Label>
        <Select value={scope} onValueChange={v => setScope(v as 'user' | 'org')} disabled={!data.is_admin}><SelectTrigger className="w-full" id="add-scope"><SelectValue /></SelectTrigger>
          <SelectContent><SelectItem value="user">{t('approvals.scope.user')}</SelectItem><SelectItem value="org">{t('approvals.scope.org')}</SelectItem></SelectContent></Select></div>
      <div className="space-y-1.5"><Label htmlFor="add-name">{t('approvals.name')}<span className="text-muted-foreground"> · {t('approvals.optional')}</span></Label>
        <Input id="add-name" value={name} onChange={e => setName(e.target.value)} placeholder={t('approvals.namePh')} /></div>
    </div>
    <p className="text-xs text-muted-foreground">{t(`approvals.help.${kind}`)} {data.is_admin ? t('approvals.scopeHelpAdmin') : t('approvals.scopeHelp')}</p>
    <SecretFields k={k} vals={vals} setVals={setVals} idp={`add-${kind}`} />
    {alerts}
    <div className="flex justify-end"><Button size="sm" id="add-save" disabled={!k.fields.some(f => !k.optional.includes(f) && vals[f]?.trim())}
      onClick={() => run(() => api('/api/approvals/channels', { method: 'POST', json: { kind, scope, name, ...vals } }), t('approvals.saved'))}><Save />{t('approvals.save')}</Button></div>
  </div>
}

type Identity = { external_id: string; verified: boolean; code_pending: boolean; code_expires: number | null } | null

/** One chat account: link -> the bot DMs a one-time code -> type it back -> verified (only then do button presses count). */
function IdentityRow({ kind, value, onChange }: { kind: string; value: Identity; onChange: (ids: Record<string, Identity>) => void }) {
  const { t } = useTranslation()
  const [ext, setExt] = useState(value?.external_id || ''); const [code, setCode] = useState(''); const [err, setErr] = useState(''); const [busy, setBusy] = useState(false)
  const call = async (path: string, init: Parameters<typeof api>[1]) => {
    setErr(''); setBusy(true)
    try { onChange(await api<Record<string, Identity>>(path, init)); return true } catch (e: any) { setErr(e.message); return false } finally { setBusy(false) }
  }
  const linkAndSend = async () => {
    if (await call('/api/approvals/identities', { method: 'PUT', json: { [kind]: ext.trim() } }) && ext.trim()) await call(`/api/approvals/identities/${kind}/send-code`, { method: 'POST' })
  }
  const changed = ext.trim() !== (value?.external_id || '')
  return <div className="space-y-2 rounded-lg border p-4" data-testid={`identity-${kind}`}>
    <div className="flex items-center gap-2">
      <Label htmlFor={`id-${kind}`}>{t(`approvals.identity.${kind}`)}</Label>
      {value && (value.verified ? <Badge id={`id-${kind}-verified`}><ShieldCheck />{t('approvals.verified')}</Badge> : <Badge variant="outline">{t('approvals.unverified')}</Badge>)}
    </div>
    <div className="flex gap-2">
      <Input id={`id-${kind}`} className="font-mono" value={ext} placeholder={t(`approvals.identityPh.${kind}`)} onChange={e => setExt(e.target.value)} />
      <Button size="sm" variant={changed || !value?.verified ? 'default' : 'outline'} id={`id-${kind}-link`} disabled={busy || (!changed && !!value?.verified) || (!changed && !ext.trim())}
        onClick={linkAndSend}><Send />{ext.trim() ? t('approvals.linkSend') : t('approvals.unlink')}</Button>
    </div>
    <p className="text-xs text-muted-foreground">{t(`approvals.identityHow.${kind}`)}</p>
    {value && !value.verified && !changed && <div className="space-y-1.5">
      <Label htmlFor={`id-${kind}-code`} className="text-xs">{value.code_pending ? t('approvals.codeSent') : t('approvals.codeNeeded')}</Label>
      <div className="flex flex-wrap gap-2">
        <Input id={`id-${kind}-code`} className="w-36 font-mono tracking-widest" inputMode="numeric" maxLength={6} placeholder="123456" value={code} onChange={e => setCode(e.target.value.replace(/\D/g, ''))} />
        <Button size="sm" id={`id-${kind}-verify`} disabled={busy || code.length !== 6}
          onClick={async () => { if (await call(`/api/approvals/identities/${kind}/verify`, { method: 'POST', json: { code } })) setCode('') }}><ShieldCheck />{t('approvals.verify')}</Button>
        <Button size="sm" variant="ghost" id={`id-${kind}-resend`} disabled={busy} onClick={() => call(`/api/approvals/identities/${kind}/send-code`, { method: 'POST' })}><RotateCw />{t('approvals.resend')}</Button>
      </div>
      {kind === 'telegram' && <p className="text-xs text-muted-foreground">{t('approvals.telegramStart')}</p>}
    </div>}
    {err && <Alert variant="destructive"><AlertCircle /><AlertDescription>{err}</AlertDescription></Alert>}
  </div>
}

function Identities() {
  const { t } = useTranslation()
  const [ids, setIds] = useState<Record<string, Identity> | null>(null); const [err, setErr] = useState('')
  useEffect(() => { api<Record<string, Identity>>('/api/approvals/identities').then(setIds).catch(e => setErr(e.message)) }, [])
  return <div className="space-y-3">
    <p className="text-sm text-muted-foreground">{t('approvals.identitiesHelp')}</p>
    {err && <Alert variant="destructive"><AlertCircle /><AlertDescription>{err}</AlertDescription></Alert>}
    {ids && Object.keys(ids).map(k => <IdentityRow key={k} kind={k} value={ids[k]} onChange={setIds} />)}
  </div>
}

function AuditLog() {
  const { t } = useTranslation(); const [items, setItems] = useState<Audit[] | null>(null); const [err, setErr] = useState('')
  useEffect(() => { api<Audit[]>('/api/approvals/audit').then(setItems).catch(e => setErr(e.message)) }, [])
  if (err) return <Alert variant="destructive"><AlertCircle /><AlertDescription>{err}</AlertDescription></Alert>
  if (items && !items.length) return <p className="text-sm text-muted-foreground" id="audit-empty">{t('approvals.auditEmpty')}</p>
  return <Table id="approval-audit">
    <TableHeader><TableRow><TableHead>{t('approvals.col.when')}</TableHead><TableHead>{t('approvals.col.action')}</TableHead><TableHead>{t('approvals.col.who')}</TableHead><TableHead>{t('approvals.col.run')}</TableHead></TableRow></TableHeader>
    <TableBody>{(items || []).map(e => <TableRow key={e.id} data-testid="audit-row">
      <TableCell className="whitespace-nowrap text-xs text-muted-foreground">{new Date(e.at * 1000).toLocaleString(i18n.resolvedLanguage)}</TableCell>
      <TableCell className="whitespace-normal"><div className="flex max-w-56 flex-col items-start gap-1"><Badge variant={ACTION_VARIANT[e.action] || 'secondary'}>{t(`approvals.action.${e.action}`)}</Badge>
        {e.code && <span className="text-xs text-muted-foreground">{errorText({ code: e.code, details: { kind: t(`approvals.kind.${e.kind}`) } })}</span>}</div></TableCell>
      <TableCell className="whitespace-normal text-xs"><div className="max-w-40 truncate">{e.actor || '—'}</div><div className="text-muted-foreground">{t(`approvals.kind.${e.kind}`)}{e.external_id && <span className="font-mono"> · {e.external_id}</span>}</div></TableCell>
      <TableCell className="text-xs"><div className="max-w-40 truncate">{e.workflow_name || '—'}</div><div className="font-mono text-muted-foreground">{e.run_id}</div></TableCell>
    </TableRow>)}</TableBody>
  </Table>
}

/** Approval through Slack / Telegram (TASK-0022): connections (personal + org-wide), my verified chat accounts, audit log. */
export function ApprovalChannelsDialog({ open, onOpenChange }: { open: boolean; onOpenChange: (o: boolean) => void }) {
  const { t } = useTranslation(); const [data, setData] = useState<Channels | null>(null); const [err, setErr] = useState('')
  const load = () => api<Channels>('/api/approvals/channels').then(d => { setData(d); setErr('') }).catch(e => setErr(e.message))
  useEffect(() => { if (open) load() }, [open])
  return <Dialog open={open} onOpenChange={onOpenChange}>
    <DialogContent className="flex max-h-[90dvh] flex-col overflow-hidden sm:max-w-3xl" id="approvals-dialog">
      <DialogHeader className="shrink-0"><DialogTitle>{t('approvals.title')}</DialogTitle><DialogDescription>{t('approvals.description')}</DialogDescription></DialogHeader>
      <Tabs defaultValue="channels" className="flex min-h-0 flex-1 flex-col">
        <TabsList className="shrink-0"><TabsTrigger value="channels" id="approvals-tab-channels">{t('approvals.tab.channels')}</TabsTrigger>
          <TabsTrigger value="accounts" id="approvals-tab-accounts">{t('approvals.tab.accounts')}</TabsTrigger>
          <TabsTrigger value="audit" id="approvals-tab-audit">{t('approvals.tab.audit')}</TabsTrigger></TabsList>
        <div className="-mx-1 min-h-0 flex-1 space-y-4 overflow-y-auto px-1">
          {err && <Alert variant="destructive"><AlertCircle /><AlertDescription>{err}</AlertDescription></Alert>}
          <TabsContent value="channels" className="space-y-4">
            {data && !data.channels.length && <p className="text-sm text-muted-foreground" id="channels-empty">{t('approvals.noChannels')}</p>}
            {data?.channels.map(c => { const k = data.kinds.find(x => x.kind === c.kind); return k && <ChannelCard key={c.id} c={c} k={k} publicUrl={data.public_url} onChange={load} /> })}
            {data && <AddChannel data={data} onChange={load} />}</TabsContent>
          <TabsContent value="accounts"><Identities /></TabsContent>
          <TabsContent value="audit"><AuditLog /></TabsContent>
        </div>
      </Tabs>
    </DialogContent>
  </Dialog>
}
