import { useEffect, useState } from 'react'
import { KeyRound, Plus, Trash2, AlertCircle, Lock } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { api } from '@/lib/api'

export type Credential = { id: string; name: string; provider: string; base_url: string | null; hint: string; created: number }

export function CredentialsDialog() {
  const [open, setOpen] = useState(false)
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
    <DialogTrigger asChild><Button variant="outline" id="creds-btn"><KeyRound />Credentials</Button></DialogTrigger>
    <DialogContent className="sm:max-w-xl">
      <DialogHeader><DialogTitle>LLM credentials</DialogTitle>
        <DialogDescription className="flex items-center gap-1"><Lock className="size-3" />API key được mã hoá khi lưu (Fernet) và không bao giờ được trả về trình duyệt.</DialogDescription></DialogHeader>
      <div className="space-y-2">
        {items.map(c => <div key={c.id} className="flex items-center gap-2 rounded-md border px-3 py-2 text-sm">
          <Badge variant="secondary">{c.provider}</Badge><span className="font-medium">{c.name}</span>
          <span className="font-mono text-xs text-muted-foreground">{c.hint}</span>
          {c.base_url && <span className="truncate text-xs text-muted-foreground">{c.base_url}</span>}
          <Button variant="ghost" size="icon" className="ml-auto size-7" onClick={() => del(c.id)}><Trash2 /></Button></div>)}
        {!items.length && <p className="text-xs text-muted-foreground">Chưa có credential. Không có credential → LLM node chạy mock.</p>}
      </div>
      <div className="grid grid-cols-2 gap-3 border-t pt-3">
        <div className="space-y-1.5"><Label>Tên</Label><Input value={name} onChange={e => setName(e.target.value)} placeholder="OpenAI cá nhân" /></div>
        <div className="space-y-1.5"><Label>Provider</Label><Select value={provider} onValueChange={setProvider}><SelectTrigger className="w-full"><SelectValue /></SelectTrigger>
          <SelectContent><SelectItem value="openai">OpenAI / compatible</SelectItem><SelectItem value="anthropic">Anthropic</SelectItem></SelectContent></Select></div>
        <div className="space-y-1.5 col-span-2"><Label>API key</Label><Input type="password" autoComplete="off" value={key} onChange={e => setKey(e.target.value)} /></div>
        <div className="space-y-1.5 col-span-2"><Label>Base URL (tuỳ chọn, cho endpoint OpenAI-compatible)</Label><Input value={baseUrl} onChange={e => setBaseUrl(e.target.value)} placeholder="https://api.openai.com/v1" /></div>
      </div>
      {err && <div className="flex items-center gap-2 rounded-md border border-destructive/50 bg-destructive/10 px-3 py-2 text-sm text-destructive"><AlertCircle className="size-4" />{err}</div>}
      <div className="flex justify-end"><Button onClick={add} disabled={!key.trim()}><Plus />Thêm credential</Button></div>
    </DialogContent>
  </Dialog>
}
