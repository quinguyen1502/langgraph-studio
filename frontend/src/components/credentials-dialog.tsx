import { useTranslation } from 'react-i18next'
import { useEffect, useState } from 'react'
import { KeyRound, Plus, Trash2, AlertCircle, Lock, PlugZap, CircleCheck, Info, Loader2 } from 'lucide-react'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { useConfirmDelete } from '@/components/confirm-delete-dialog'
import { api } from '@/lib/api'
import { credentialModels, probeProvider, useProviders, type ProbeResult } from '@/lib/providers'

export type Credential = { id: string; name: string; provider: string; base_url: string | null; hint: string; headers?: Record<string, string>; created: number }
type Status = { busy?: boolean; ok?: ProbeResult; err?: string }

/** Result of 'Test connection' (form or saved row): success badge with model count, or the translated error. */
function ProbeStatus({ s, id }: { s: Status; id: string }) {
  const { t } = useTranslation()
  if (s.busy) return <span className="flex items-center gap-1 text-xs text-muted-foreground"><Loader2 className="size-3 animate-spin" />{t('creds.testing')}</span>
  if (s.ok) return <Badge variant="success" id={id}><CircleCheck />{t('creds.testOk', { count: s.ok.models.length, ms: s.ok.latency_ms })}</Badge>
  if (s.err) return <Alert variant="destructive" id={id}><AlertCircle /><AlertDescription>{s.err}</AlertDescription></Alert>
  return null
}

const run = async (set: (s: Status) => void, fn: () => Promise<ProbeResult>) => {
  set({ busy: true })
  try { set({ ok: await fn() }) } catch (e: any) { set({ err: e.message }) }
}

export function CredentialsDialog() {
  const { t } = useTranslation(); const [open, setOpen] = useState(false)
  const providers = useProviders()
  const [items, setItems] = useState<Credential[]>([])
  const [name, setName] = useState(''); const [provider, setProvider] = useState('openai')
  const [key, setKey] = useState(''); const [baseUrl, setBaseUrl] = useState(''); const [headers, setHeaders] = useState<Record<string, string>>({})
  const [err, setErr] = useState(''); const [test, setTest] = useState<Status>({}); const [rowTest, setRowTest] = useState<Record<string, Status>>({})
  const p = providers.find(x => x.id === provider)
  const load = () => api<Credential[]>('/api/credentials').then(setItems)
  useEffect(() => { if (open) load() }, [open])
  const pick = (v: string) => { setProvider(v); setKey(''); setBaseUrl(''); setHeaders({}); setTest({}); setErr('') }  // never carry a key to another provider
  const form = () => ({ api_key: key, base_url: baseUrl || null, headers })
  const add = async () => {
    setErr('')
    try { await api('/api/credentials', { method: 'POST', json: { name, provider, ...form() } }); setName(''); setKey(''); setBaseUrl(''); setHeaders({}); setTest({}); load() }
    catch (e: any) { setErr(e.message) }
  }
  const confirmDel = useConfirmDelete()
  const del = (c: Credential) => confirmDel.ask({ title: t('creds.deleteTitle', { name: c.name }), name: c.name, description: t('creds.deleteBody'),
    onConfirm: async () => { await api(`/api/credentials/${c.id}`, { method: 'DELETE' }); load() } })
  const label = (id: string) => t(`creds.providers.${id}`, { defaultValue: providers.find(x => x.id === id)?.label ?? id })
  return <Dialog open={open} onOpenChange={setOpen}>
    <DialogTrigger asChild><Button variant="outline" id="creds-btn"><KeyRound />{t('creds.button')}</Button></DialogTrigger>
    <DialogContent className="sm:max-w-2xl max-h-[90vh] overflow-y-auto">
      <DialogHeader><DialogTitle>{t('creds.title')}</DialogTitle>
        <DialogDescription className="flex items-center gap-1"><Lock className="size-3" />{t('creds.desc')}</DialogDescription></DialogHeader>
      <div className="space-y-2">
        {items.map(c => <div key={c.id} className="space-y-2 rounded-md border px-3 py-2 text-sm" data-cred={c.name}>
          <div className="flex items-center gap-2">
            <Badge variant="secondary">{label(c.provider)}</Badge><span className="font-medium">{c.name}</span>
            {c.hint && <span className="font-mono text-xs text-muted-foreground">{c.hint}</span>}
            {c.base_url && <span className="truncate text-xs text-muted-foreground">{c.base_url}</span>}
            <div className="ml-auto flex items-center gap-1">
              <Button variant="ghost" size="sm" aria-label={t('creds.testAria', { name: c.name })}
                onClick={() => run(s => setRowTest(r => ({ ...r, [c.id]: s })), () => credentialModels(c.id))}><PlugZap />{t('creds.test')}</Button>
              <Button variant="ghost" size="icon" className="size-7" aria-label={t('creds.deleteAria', { name: c.name })} onClick={() => del(c)}><Trash2 /></Button>
            </div></div>
          {rowTest[c.id] && <ProbeStatus s={rowTest[c.id]} id={`cred-test-${c.id}`} />}
        </div>)}
        {!items.length && <p className="text-xs text-muted-foreground">{t('creds.empty')}</p>}
      </div>
      <div className="grid grid-cols-2 gap-3 border-t pt-3">
        <div className="space-y-1.5"><Label htmlFor="cred-name">{t('creds.name')}</Label><Input id="cred-name" value={name} onChange={e => setName(e.target.value)} placeholder={t('creds.namePh')} /></div>
        <div className="space-y-1.5"><Label>{t('creds.provider')}</Label><Select value={provider} onValueChange={pick}><SelectTrigger className="w-full" id="cred-provider"><SelectValue /></SelectTrigger>
          <SelectContent>{providers.map(x => <SelectItem key={x.id} value={x.id}>{label(x.id)}</SelectItem>)}</SelectContent></Select></div>
        <div className="space-y-1.5 col-span-2"><Label htmlFor="cred-key">{p && !p.key_required ? t('creds.keyOptional') : t('creds.key')}</Label>
          <Input id="cred-key" type="password" autoComplete="off" value={key} onChange={e => setKey(e.target.value)} /></div>
        <div className="space-y-1.5 col-span-2"><Label htmlFor="cred-base">{t('creds.baseUrl')}</Label>
          <Input id="cred-base" value={baseUrl} onChange={e => setBaseUrl(e.target.value)} placeholder={p?.default_base_url ?? 'https://api.openai.com/v1'} />
          {p?.local && <p className="flex items-start gap-1 text-xs text-muted-foreground" id="cred-docker-hint"><Info className="mt-0.5 size-3 shrink-0" />{t('creds.dockerHint')}</p>}</div>
        {p?.header_fields.map(h => <div key={h} className="space-y-1.5"><Label htmlFor={`cred-h-${h}`}>{t('creds.header', { name: h })}</Label>
          <Input id={`cred-h-${h}`} value={headers[h] ?? ''} onChange={e => setHeaders({ ...headers, [h]: e.target.value })}
            placeholder={t(h === 'X-Title' ? 'creds.titlePh' : 'creds.refererPh')} /></div>)}
      </div>
      <ProbeStatus s={test} id="cred-test-result" />
      {err && <Alert variant="destructive" id="cred-error"><AlertCircle /><AlertDescription>{err}</AlertDescription></Alert>}
      <div className="flex justify-end gap-2">
        <Button variant="outline" id="cred-test" disabled={test.busy || (!!p?.key_required && !key.trim())} onClick={() => run(setTest, () => probeProvider(provider, form()))}><PlugZap />{t('creds.test')}</Button>
        <Button onClick={add} id="cred-add" disabled={!!p?.key_required && !key.trim()}><Plus />{t('creds.add')}</Button></div>
    </DialogContent>
    {confirmDel.dialog}
  </Dialog>
}
