/** Share a workflow (TASK-0014): owner or admin adds users by email as viewer (open, run) or editor (also edit). */
import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Loader2, Share2, Trash2, UserPlus } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { api } from '@/lib/api'
import type { Shares } from '@/lib/rbac'

export function ShareDialog({ workflowId, disabled }: { workflowId: string; disabled?: boolean }) {
  const { t } = useTranslation()
  const [open, setOpen] = useState(false); const [data, setData] = useState<Shares | null>(null)
  const [email, setEmail] = useState(''); const [role, setRole] = useState<'viewer' | 'editor'>('viewer')
  const [err, setErr] = useState(''); const [busy, setBusy] = useState(false)
  const load = () => api<Shares>(`/api/workflows/${workflowId}/shares`).then(setData).catch(e => setErr(e.message))
  useEffect(() => { if (open) { setErr(''); load() } }, [open, workflowId])
  const run = async (f: () => Promise<any>) => { setBusy(true); setErr(''); try { await f() } catch (e: any) { setErr(e.message) } finally { setBusy(false) } }
  const add = () => run(async () => { setData(await api(`/api/workflows/${workflowId}/shares`, { method: 'PUT', json: { email: email.trim(), role } })); setEmail('') })
  const change = (em: string, r: string) => run(async () => setData(await api(`/api/workflows/${workflowId}/shares`, { method: 'PUT', json: { email: em, role: r } })))
  const remove = (uid: string) => run(async () => { await api(`/api/workflows/${workflowId}/shares/${uid}`, { method: 'DELETE' }); await load() })
  return <Dialog open={open} onOpenChange={setOpen}>
    <DialogTrigger asChild><Button variant="outline" size="sm" id="share-btn" disabled={disabled}><Share2 />{t('share.button')}</Button></DialogTrigger>
    <DialogContent className="sm:max-w-lg">
      <DialogHeader><DialogTitle>{t('share.title')}</DialogTitle><DialogDescription>{t('share.intro')}</DialogDescription></DialogHeader>
      {data?.can_share && <div className="flex items-end gap-2">
        <div className="flex-1 space-y-1.5"><Label htmlFor="share-email">{t('share.email')}</Label>
          <Input id="share-email" type="email" placeholder="name@example.com" value={email} onChange={e => setEmail(e.target.value)} onKeyDown={e => e.key === 'Enter' && email.trim() && add()} /></div>
        <Select value={role} onValueChange={v => setRole(v as 'viewer' | 'editor')}><SelectTrigger className="w-32" id="share-role" aria-label={t('share.role')}><SelectValue /></SelectTrigger>
          <SelectContent><SelectItem value="viewer">{t('share.roles.viewer')}</SelectItem><SelectItem value="editor">{t('share.roles.editor')}</SelectItem></SelectContent></Select>
        <Button id="share-add" onClick={add} disabled={!email.trim() || busy}>{busy ? <Loader2 className="animate-spin" /> : <UserPlus />}{t('share.add')}</Button>
      </div>}
      {err && <p role="alert" className="text-sm text-destructive" id="share-error">{err}</p>}
      <ul className="divide-y rounded-md border" id="share-list">
        {data && <li className="flex items-center gap-2 px-3 py-2 text-sm"><span className="flex-1 truncate">{data.owner.email}</span><Badge variant="secondary">{t('share.owner')}</Badge></li>}
        {data?.shares.map(s => <li key={s.user_id} className="flex items-center gap-2 px-3 py-2 text-sm share-row">
          <span className="flex-1 truncate">{s.email}</span>
          {data.can_share ? <>
            <Select value={s.role} onValueChange={v => change(s.email, v)}><SelectTrigger size="sm" className="w-28" aria-label={t('share.roleFor', { email: s.email })}><SelectValue /></SelectTrigger>
              <SelectContent><SelectItem value="viewer">{t('share.roles.viewer')}</SelectItem><SelectItem value="editor">{t('share.roles.editor')}</SelectItem></SelectContent></Select>
            <Button variant="ghost" size="icon" aria-label={t('share.remove', { email: s.email })} onClick={() => remove(s.user_id)} disabled={busy}><Trash2 /></Button>
          </> : <Badge variant="outline">{t(`share.roles.${s.role}`)}</Badge>}
        </li>)}
        {data && !data.shares.length && <li className="px-3 py-3 text-sm text-muted-foreground" id="share-empty">{t('share.empty')}</li>}
      </ul>
    </DialogContent>
  </Dialog>
}
