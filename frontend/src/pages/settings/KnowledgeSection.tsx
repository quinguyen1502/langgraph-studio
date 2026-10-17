/** Knowledge bases (TASK-0012): create, upload txt/md/pdf, list documents, test a search, re-index, delete.
 *  Retriever nodes pick one of these by id. */
import { useEffect, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { ChevronDown, Database, FileText, Plus, RefreshCw, Search, Settings2, Trash2, Upload } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardAction, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Separator } from '@/components/ui/separator'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { ErrorAlert, useAction } from '@/components/approvals/channel-parts'
import type { Credential } from '@/components/credentials-dialog'
import { api } from '@/lib/api'
import { KB_ACCEPT, fmtBytes, type KbHit, type KnowledgeBase } from '@/lib/knowledge'
import { cn } from '@/lib/utils'

type Form = { name: string; description: string; model: string; credential_id: string }
const toForm = (kb?: KnowledgeBase): Form => ({ name: kb?.name || '', description: kb?.description || '', model: kb?.model || 'text-embedding-3-small', credential_id: kb?.credential_id || '' })

function KbFields({ form, set, creds, idp }: { form: Form; set: (f: Form) => void; creds: Credential[]; idp: string }) {
  const { t } = useTranslation()
  const openai = creds.filter(c => c.provider === 'openai')
  return <div className="grid gap-3 sm:grid-cols-2">
    <div className="space-y-1.5"><Label htmlFor={`${idp}-name`}>{t('kb.name')}</Label><Input id={`${idp}-name`} value={form.name} onChange={e => set({ ...form, name: e.target.value })} /></div>
    <div className="space-y-1.5"><Label htmlFor={`${idp}-description`}>{t('kb.description')}</Label><Input id={`${idp}-description`} value={form.description} onChange={e => set({ ...form, description: e.target.value })} /></div>
    <div className="space-y-1.5"><Label htmlFor={`${idp}-model`}>{t('kb.model')}</Label><Input id={`${idp}-model`} className="font-mono text-xs" value={form.model} onChange={e => set({ ...form, model: e.target.value })} /></div>
    <div className="space-y-1.5"><Label htmlFor={`${idp}-credential`}>{t('kb.credential')}</Label>
      <Select value={form.credential_id || 'none'} onValueChange={v => set({ ...form, credential_id: v === 'none' ? '' : v })}>
        <SelectTrigger className="w-full" id={`${idp}-credential`}><SelectValue /></SelectTrigger>
        <SelectContent><SelectItem value="none">{t('kb.credentialDefault')}</SelectItem>
          {openai.map(c => <SelectItem key={c.id} value={c.id}>{c.name} · {c.hint}</SelectItem>)}</SelectContent></Select></div>
  </div>
}

function KbCard({ kb, creds, reload, defaultOpen }: { kb: KnowledgeBase; creds: Credential[]; reload: () => void; defaultOpen: boolean }) {
  const { t } = useTranslation(); const [open, setOpen] = useState(defaultOpen)
  const [full, setFull] = useState<KnowledgeBase | null>(null); const [form, setForm] = useState(toForm(kb))
  const [edit, setEdit] = useState(false); const [q, setQ] = useState(''); const [hits, setHits] = useState<KbHit[] | null>(null)
  const file = useRef<HTMLInputElement>(null)
  const load = () => api<KnowledgeBase>(`/api/knowledge-bases/${kb.id}`).then(setFull)
  const done = () => { load(); reload() }
  const act = useAction(done)
  useEffect(() => { if (open) load() }, [open, kb.documents, kb.chunks])
  const upload = (f?: File) => { if (!f) return; const fd = new FormData(); fd.append('file', f)
    act.run(() => api(`/api/knowledge-bases/${kb.id}/documents`, { method: 'POST', body: fd }), r => t('kb.uploaded', { name: r.filename, chunks: r.chunks }))
    if (file.current) file.current.value = '' }
  const search = () => act.run(() => api<KbHit[]>(`/api/knowledge-bases/${kb.id}/search`, { method: 'POST', json: { query: q, top_k: 4 } }).then(setHits), '')
  const files = full?.files || []
  return <Collapsible open={open} onOpenChange={setOpen} asChild>
    <Card data-testid={`kb-card-${kb.id}`} className="gap-4">
      <CardHeader>
        <CardTitle className="flex flex-wrap items-center gap-2"><Database className="size-4 text-node-retriever" />{kb.name}
          <Badge variant="secondary" data-testid="kb-docs">{t('kb.documents', { count: kb.documents })}</Badge>
          <Badge variant="outline">{t('kb.chunks', { count: kb.chunks })}</Badge>
          {kb.embedder && <Badge variant="outline" className="font-mono">{kb.embedder}</Badge>}
        </CardTitle>
        <CardDescription>{kb.description || t('kb.noDescription')}</CardDescription>
        <CardAction><CollapsibleTrigger asChild><Button variant="ghost" size="icon" aria-label={t('settings.toggle')} id={`kb-${kb.id}-toggle`}>
          <ChevronDown className={cn('transition-transform', open && 'rotate-180')} /></Button></CollapsibleTrigger></CardAction>
      </CardHeader>
      <CollapsibleContent>
        <CardContent className="space-y-4">
          {act.alerts}
          <div className="flex flex-wrap items-center gap-2">
            <input ref={file} type="file" accept={KB_ACCEPT} className="hidden" id={`kb-${kb.id}-file`} onChange={e => upload(e.target.files?.[0])} />
            <Button size="sm" disabled={act.busy} onClick={() => file.current?.click()} id={`kb-${kb.id}-upload`}><Upload />{t('kb.upload')}</Button>
            <span className="text-xs text-muted-foreground">{t('kb.uploadHelp')}</span>
            <Button size="sm" variant="ghost" className={cn('ml-auto', edit && 'bg-accent text-accent-foreground')} onClick={() => setEdit(!edit)} aria-expanded={edit} id={`kb-${kb.id}-settings`}><Settings2 />{t('kb.settings')}</Button>
          </div>
          {edit && <div className="space-y-3 rounded-md border p-4" data-testid="kb-settings">
            <KbFields form={form} set={setForm} creds={creds} idp={`kb-${kb.id}`} />
            <p className="text-xs text-muted-foreground">{t('kb.embedHelp')}</p>
            <div className="flex flex-wrap gap-2">
              <Button size="sm" disabled={act.busy} onClick={() => act.run(() => api(`/api/knowledge-bases/${kb.id}`, { method: 'PUT', json: { ...form, credential_id: form.credential_id || null } }), t('kb.saved'))}>{t('common.save')}</Button>
              <Button size="sm" variant="outline" disabled={act.busy} onClick={() => act.run(() => api(`/api/knowledge-bases/${kb.id}/reindex`, { method: 'POST' }), r => t('kb.reindexed', { count: r.chunks }))}><RefreshCw />{t('kb.reindex')}</Button>
              <Button size="sm" variant="destructive" className="ml-auto" disabled={act.busy} id={`kb-${kb.id}-delete`}
                onClick={() => { if (confirm(t('kb.confirmDelete', { name: kb.name }))) act.run(() => api(`/api/knowledge-bases/${kb.id}`, { method: 'DELETE' }), '') }}><Trash2 />{t('kb.delete')}</Button>
            </div>
          </div>}
          {files.length ? <div className="rounded-md border"><Table>
            <TableHeader><TableRow><TableHead>{t('kb.file')}</TableHead><TableHead className="text-right">{t('kb.size')}</TableHead><TableHead className="text-right">{t('kb.chunkCol')}</TableHead><TableHead /></TableRow></TableHeader>
            <TableBody>{files.map(f => <TableRow key={f.id} data-testid="kb-file">
              <TableCell><span className="flex items-center gap-2"><FileText className="size-4 text-muted-foreground" />{f.filename}</span></TableCell>
              <TableCell className="text-right text-xs text-muted-foreground">{fmtBytes(f.size)}</TableCell>
              <TableCell className="text-right text-xs">{f.chunks}</TableCell>
              <TableCell className="w-10"><Button variant="ghost" size="icon" aria-label={t('kb.deleteFile')} onClick={() => act.run(() => api(`/api/knowledge-bases/${kb.id}/documents/${f.id}`, { method: 'DELETE' }), t('kb.fileDeleted'))}><Trash2 /></Button></TableCell>
            </TableRow>)}</TableBody></Table></div>
            : <p className="text-sm text-muted-foreground" data-testid="kb-empty">{t('kb.noFiles')}</p>}
          <Separator />
          <div className="space-y-2">
            <h3 className="text-sm font-medium">{t('kb.testSearch')}</h3>
            <form className="flex gap-2" onSubmit={e => { e.preventDefault(); search() }}>
              <Input id={`kb-${kb.id}-query`} value={q} onChange={e => setQ(e.target.value)} placeholder={t('kb.queryPlaceholder')} />
              <Button type="submit" variant="outline" disabled={act.busy || !q.trim()} id={`kb-${kb.id}-search`}><Search />{t('kb.search')}</Button>
            </form>
            {hits && (hits.length ? <ol className="space-y-2" data-testid="kb-hits">{hits.map((h, i) => <li key={i} className="rounded-md border p-3 text-sm">
              <div className="mb-1 flex items-center gap-2 text-xs text-muted-foreground"><Badge variant="secondary" className="font-mono">{h.score.toFixed(3)}</Badge>{h.filename} · #{h.index + 1}</div>
              <p className="line-clamp-3 whitespace-pre-line">{h.text}</p></li>)}</ol>
              : <p className="text-sm text-muted-foreground">{t('kb.noHits')}</p>)}
          </div>
        </CardContent>
      </CollapsibleContent>
    </Card>
  </Collapsible>
}

export function KnowledgeSection() {
  const { t } = useTranslation()
  const [items, setItems] = useState<KnowledgeBase[] | null>(null); const [err, setErr] = useState('')
  const [creds, setCreds] = useState<Credential[]>([]); const [adding, setAdding] = useState(false); const [form, setForm] = useState(toForm())
  const load = () => api<KnowledgeBase[]>('/api/knowledge-bases').then(d => { setItems(d); setErr('') }).catch(e => setErr(e.message))
  const create = useAction(() => { setAdding(false); setForm(toForm()); load() })
  useEffect(() => { load(); api<Credential[]>('/api/credentials').then(setCreds).catch(() => {}) }, [])
  return <div className="space-y-4">
    {err && <ErrorAlert>{err}</ErrorAlert>}
    {adding ? <Card className="gap-4" id="kb-new"><CardHeader><CardTitle>{t('kb.new')}</CardTitle><CardDescription>{t('kb.newHelp')}</CardDescription></CardHeader>
      <CardContent className="space-y-3">{create.alerts}
        <KbFields form={form} set={setForm} creds={creds} idp="kb-new" />
        <div className="flex gap-2"><Button size="sm" disabled={create.busy} id="kb-create" onClick={() => create.run(() => api('/api/knowledge-bases', { method: 'POST', json: { ...form, credential_id: form.credential_id || null } }), '')}>{t('kb.create')}</Button>
          <Button size="sm" variant="ghost" onClick={() => setAdding(false)}>{t('common.cancel')}</Button></div></CardContent></Card>
      : <Button size="sm" onClick={() => setAdding(true)} id="kb-add"><Plus />{t('kb.new')}</Button>}
    {items && !items.length && !adding && <p className="text-sm text-muted-foreground" id="kb-none">{t('kb.none')}</p>}
    {items?.map((kb, i) => <KbCard key={kb.id} kb={kb} creds={creds} reload={load} defaultOpen={i === 0} />)}
  </div>
}
