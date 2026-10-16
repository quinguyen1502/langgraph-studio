import { useTranslation } from 'react-i18next'
import { useEffect, useState } from 'react'
import { KeyRound, Plus, Trash2, AlertCircle, Lock } from 'lucide-react'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { api } from '@/lib/api'

export type Credential = { id: string; name: string; provider: string; base_url: string | null; hint: string; created: number }

export function CredentialsDialog() {
  const { t } = useTranslation(); const [open, setOpen] = useState(false)
  const [items, setItems] = useState<Credential[]>([])
  const [name, setName] = useState(''); const [provider, setProvider] = useState('openai')
  const [key, setKey] = useState(''); const [baseUrl, setBaseUrl] = useState(''); const [err, setErr] = useState('')
  const load = () => api<Credential[]>('/api/credentials').then(setItems)
  useEffect(() => { if (open) load() }, [open])
  const add = async () => {
    setErr('')
    try { await api('/api/credentials', { method: 'POST', json: { name, provider, api_key: key, base_url: baseUrl || null } }); setName(''); setKey(''); setBaseUrl(''); load() }
    catch (e: any) { setErr(e.message) }
  }
  const del = async (id: string) => { await api(`/api/credentials/${id}`, { method: 'DELETE' }); load() }
  return <Dialog open={open} onOpenChange={setOpen}>
    <DialogTrigger asChild><Button variant="outline" id="creds-btn"><KeyRound />{t('creds.button')}</Button></DialogTrigger>
    <DialogContent className="sm:max-w-xl">
      <DialogHeader><DialogTitle>{t('creds.title')}</DialogTitle>
        <DialogDescription className="flex items-center gap-1"><Lock className="size-3" />{t('creds.desc')}</DialogDescription></DialogHeader>
      <div className="space-y-2">
        {items.map(c => <div key={c.id} className="flex items-center gap-2 rounded-md border px-3 py-2 text-sm">
          <Badge variant="secondary">{c.provider}</Badge><span className="font-medium">{c.name}</span>
          <span className="font-mono text-xs text-muted-foreground">{c.hint}</span>
          {c.base_url && <span className="truncate text-xs text-muted-foreground">{c.base_url}</span>}
          <Button variant="ghost" size="icon" className="ml-auto size-7" aria-label={t('creds.deleteAria', { name: c.name })} onClick={() => del(c.id)}><Trash2 /></Button></div>)}
        {!items.length && <p className="text-xs text-muted-foreground">{t('creds.empty')}</p>}
      </div>
      <div className="grid grid-cols-2 gap-3 border-t pt-3">
        <div className="space-y-1.5"><Label>{t('creds.name')}</Label><Input value={name} onChange={e => setName(e.target.value)} placeholder={t('creds.namePh')} /></div>
        <div className="space-y-1.5"><Label>{t('creds.provider')}</Label><Select value={provider} onValueChange={setProvider}><SelectTrigger className="w-full"><SelectValue /></SelectTrigger>
          <SelectContent><SelectItem value="openai">{t('creds.openai')}</SelectItem><SelectItem value="anthropic">{t('creds.anthropic')}</SelectItem></SelectContent></Select></div>
        <div className="space-y-1.5 col-span-2"><Label>{t('creds.key')}</Label><Input type="password" autoComplete="off" value={key} onChange={e => setKey(e.target.value)} /></div>
        <div className="space-y-1.5 col-span-2"><Label>{t('creds.baseUrl')}</Label><Input value={baseUrl} onChange={e => setBaseUrl(e.target.value)} placeholder="https://api.openai.com/v1" /></div>
      </div>
      {err && <Alert variant="destructive" id="cred-error"><AlertCircle /><AlertDescription>{err}</AlertDescription></Alert>}
      <div className="flex justify-end"><Button onClick={add} disabled={!key.trim()}><Plus />{t('creds.add')}</Button></div>
    </DialogContent>
  </Dialog>
}
