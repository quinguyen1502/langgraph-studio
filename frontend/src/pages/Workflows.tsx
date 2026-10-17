import { useTranslation } from 'react-i18next'
import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Workflow, Plus, Search, Copy, Pencil, Trash2, MoreHorizontal, Loader2, AlertCircle, RefreshCw, SearchX, FolderOpen, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Card } from '@/components/ui/card'
import { PendingRuns } from '@/components/pending-runs'
import { useConfirmDelete } from '@/components/confirm-delete-dialog'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator, DropdownMenuTrigger } from '@/components/ui/dropdown-menu'
import { api } from '@/lib/api'
import { fmtDate as fmt } from '@/lib/i18n'
import { LanguageSwitcher } from '@/components/language-switcher'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { ThemeToggle } from '@/lib/theme'
import { UserMenu } from '@/components/user-menu'
import { PendingBadge } from '@/components/pending-badge'
import { NotificationBell } from '@/components/notification-bell'
import { ImportDialog } from '@/components/import-dialog'
import { TemplateGallery } from '@/components/template-gallery'
import { CredentialsDialog } from '@/components/credentials-dialog'
import { Switch } from '@/components/ui/switch'
import { Label } from '@/components/ui/label'
import { can, canEdit, useMe, type Access } from '@/lib/rbac'

type Dep = { id: string | null; name: string | null }
type W = { id: string; name: string; updated: number; node_count: number; last_run_status: string | null; last_run_at: number | null; access: Access; mine: boolean; owner_email: string | null }

export function WorkflowsPage() {
  const { t } = useTranslation(); const nav = useNavigate()
  const [items, setItems] = useState<W[]>([]); const [q, setQ] = useState('')
  const [loading, setLoading] = useState(true); const [loadErr, setLoadErr] = useState('')
  const [notice, setNotice] = useState('')
  const [rename, setRename] = useState<W | null>(null); const [newName, setNewName] = useState(''); const [renameErr, setRenameErr] = useState('')
  const [busy, setBusy] = useState(false); const [gallery, setGallery] = useState(false)
  const me = useMe(); const [all, setAll] = useState(false)
  const creates = can(me, 'workflows.create')
  const load = () => api<W[]>(`/api/workflows${all ? '?all=1' : ''}`).then(w => { setItems(w); setLoadErr('') }).catch(e => setLoadErr(e.message)).finally(() => setLoading(false))
  useEffect(() => { load() }, [all])
  const flash = (m: string) => { setNotice(m); setTimeout(() => setNotice(''), 4000) }
  const create = async () => {
    setBusy(true)
    try {
      const r = await api('/api/workflows', { method: 'POST', json: { name: 'Untitled workflow', state: [{ name: 'message', type: 'string' }],
        nodes: [{ id: 'start', type: 'start', position: { x: 80, y: 200 }, data: { label: 'Start' } }, { id: 'end', type: 'end', position: { x: 480, y: 200 }, data: { label: 'End' } }],
        edges: [{ id: 'e1', source: 'start', target: 'end' }] } })
      nav(`/workflows/${r.id}`)
    } catch (e: any) { setGallery(false); flash(e.message) } finally { setBusy(false) }
  }
  const dup = async (w: W) => { try { const r = await api(`/api/workflows/${w.id}/duplicate`, { method: 'POST' }); flash(t('list.duplicated', { name: r.name })); load() } catch (e: any) { flash(e.message) } }
  const trimmed = newName.trim()
  const doRename = async () => {
    if (!rename || !trimmed || busy) return
    setBusy(true); setRenameErr('')
    try { await api(`/api/workflows/${rename.id}`, { method: 'PATCH', json: { name: trimmed } }); setRename(null); load() }
    catch (e: any) { setRenameErr(e.message) } finally { setBusy(false) }
  }
  const confirmDel = useConfirmDelete()
  const askDelete = async (w: W) => {  // dependents are listed up front; deleting then needs force
    const deps = await api<{ dependents: Dep[] }>(`/api/workflows/${w.id}/dependents`).then(r => r.dependents).catch(() => [] as Dep[])
    confirmDel.ask({ title: t('list.deleteTitle'), name: w.name, description: t('list.deleteBody', { name: w.name }),
      confirmLabel: deps.length ? t('list.deleteAnyway') : undefined,
      children: deps.length ? <Alert variant="destructive" id="delete-dependents"><AlertCircle /><AlertDescription><div>{t('list.inUse', { count: deps.length })}</div>
        <ul className="mt-1 list-disc pl-4">{deps.map((d, i) => <li key={d.id ?? i}>{d.name ?? t('list.hiddenWorkflow')}{d.id && <span className="ml-1 font-mono text-xs">{d.id}</span>}</li>)}</ul></AlertDescription></Alert> : null,
      onConfirm: async () => {
        await api(`/api/workflows/${w.id}${deps.length ? '?force=true' : ''}`, { method: 'DELETE' }); load()
      } })
  }
  const shown = useMemo(() => { const k = q.trim().toLowerCase(); return k ? items.filter(w => w.name.toLowerCase().includes(k) || w.id.includes(k)) : items }, [items, q])
  const empty = (icon: React.ReactNode, title: string, body: React.ReactNode, id: string) =>
    <TableRow className="hover:bg-transparent"><TableCell colSpan={5} className="py-14" id={id}><div className="flex flex-col items-center gap-2 text-center">
      <div className="rounded-full bg-muted p-3 text-muted-foreground">{icon}</div><div className="font-medium">{title}</div><div className="text-sm text-muted-foreground">{body}</div></div></TableCell></TableRow>

  return <div className="min-h-screen bg-background text-foreground">
    <header className="h-14 border-b flex items-center gap-3 px-6">
      <div className="flex items-center gap-2 font-semibold"><div className="rounded-md bg-primary text-primary-foreground p-1.5"><Workflow className="size-4" /></div>LangGraph Studio</div>
      <div className="ml-auto flex items-center gap-1"><PendingBadge /><NotificationBell /><LanguageSwitcher /><ThemeToggle /><UserMenu /></div>
    </header>
    <main className="max-w-6xl mx-auto p-6 space-y-4">
      <div className="flex items-end justify-between gap-4">
        <div><h1 className="text-2xl font-semibold tracking-tight">{t('list.title')}</h1><p className="text-sm text-muted-foreground" id="wf-count">{loading ? t('common.loading') : q.trim() ? t('list.filtered', { shown: shown.length, total: items.length }) : t('list.count', { count: items.length })}</p></div>
        <div className="flex gap-2">
          <div className="relative"><Search className="absolute left-2.5 top-2.5 size-4 text-muted-foreground" /><Input id="wf-search" aria-label={t('list.searchLabel')} className="pl-8 pr-8 w-64" placeholder={t('list.search')} value={q} onChange={e => setQ(e.target.value)} onKeyDown={e => e.key === 'Escape' && setQ('')} />
            {q && <Button variant="ghost" size="icon" aria-label={t('list.clearSearch')} className="absolute right-1 top-1 size-7 text-muted-foreground" onClick={() => setQ('')}><X /></Button>}</div>
          {can(me, 'workflows.all') && <div className="flex items-center gap-2 px-1"><Switch id="wf-all" checked={all} onCheckedChange={v => { setLoading(true); setAll(v) }} /><Label htmlFor="wf-all" className="text-sm font-normal whitespace-nowrap">{t('list.showAll')}</Label></div>}
          {can(me, 'resources.manage') && <CredentialsDialog />}
          {creates && <ImportDialog />}
          {creates && <Button onClick={() => setGallery(true)} id="new-wf"><Plus />{t('common.newWorkflow')}</Button>}
        </div>
      </div>
      {notice && <div role="status" id="wf-notice" className="fixed bottom-4 right-4 z-50 max-w-sm rounded-md border bg-popover text-popover-foreground shadow-md px-3 py-2 text-sm">{notice}</div>}
      {loadErr && <Alert variant="destructive" id="wf-load-error"><AlertCircle /><AlertDescription className="flex items-center gap-2">{t('list.loadError', { error: loadErr })}
        <Button size="sm" variant="outline" className="ml-auto" onClick={() => { setLoading(true); load() }}><RefreshCw />{t('common.retry')}</Button></AlertDescription></Alert>}
      <PendingRuns />
      <Card className="p-0 overflow-hidden">
        <Table>
          <TableHeader><TableRow><TableHead className="pl-4">{t('list.colName')}</TableHead><TableHead>{t('list.colNodes')}</TableHead><TableHead>{t('list.colUpdated')}</TableHead><TableHead>{t('list.colLastRun')}</TableHead><TableHead className="w-12" /></TableRow></TableHeader>
          <TableBody>
            {shown.map(w => <TableRow key={w.id} className="cursor-pointer" onClick={() => nav(`/workflows/${w.id}`)}>
              <TableCell className="pl-4 font-medium max-w-0 w-1/2"><div className="truncate" title={w.name}>{w.name}</div><div className="flex flex-wrap items-center gap-1.5 text-xs text-muted-foreground"><span className="font-mono">{w.id}</span>
                {!w.mine && <Badge variant="outline" className="wf-shared" title={w.owner_email ?? ''}>{t('list.sharedBy', { email: w.owner_email ?? '?' })}</Badge>}
                {w.access !== 'owner' && <Badge variant="secondary" className="wf-access">{t(`share.access.${w.access}`)}</Badge>}</div></TableCell>
              <TableCell><Badge variant="secondary">{w.node_count}</Badge></TableCell>
              <TableCell className="text-muted-foreground">{fmt(w.updated)}</TableCell>
              <TableCell>{w.last_run_status ? <div className="flex items-center gap-2">
                <Badge variant={w.last_run_status === 'ok' ? 'success' : w.last_run_status === 'timeout' ? 'warning' : w.last_run_status === 'cancelled' ? 'secondary' : 'destructive'}>{t(`status.${w.last_run_status}`)}</Badge>
                <span className="text-xs text-muted-foreground">{fmt(w.last_run_at!)}</span></div> : <span className="text-xs text-muted-foreground">{t('list.neverRun')}</span>}</TableCell>
              <TableCell onClick={e => e.stopPropagation()}>
                <DropdownMenu><DropdownMenuTrigger asChild><Button variant="ghost" size="icon" aria-label={t('list.actionsFor', { name: w.name })} className="wf-actions"><MoreHorizontal /></Button></DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuItem disabled={!canEdit(w.access)} onClick={() => { setRename(w); setNewName(w.name); setRenameErr('') }}><Pencil />{t('list.rename')}</DropdownMenuItem>
                    <DropdownMenuItem disabled={!creates} onClick={() => dup(w)}><Copy />{t('list.duplicate')}</DropdownMenuItem>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem variant="destructive" disabled={w.access !== 'owner'} onClick={() => askDelete(w)}><Trash2 />{t('common.delete')}</DropdownMenuItem>
                  </DropdownMenuContent></DropdownMenu>
              </TableCell>
            </TableRow>)}
            {loading && <TableRow className="hover:bg-transparent"><TableCell colSpan={5} className="py-14 text-center text-muted-foreground"><Loader2 className="inline animate-spin mr-2 size-4" />{t('list.loadingList')}</TableCell></TableRow>}
            {!loading && !loadErr && !items.length && empty(<FolderOpen className="size-5" />, t('list.emptyTitle'), <>{creates ? <>{t('list.emptyBody')} <Button size="sm" className="ml-2" onClick={create}><Plus />{t('common.newWorkflow')}</Button></> : t('list.emptyViewer')}</>, 'wf-empty')}
            {!loading && items.length > 0 && !shown.length && empty(<SearchX className="size-5" />, t('list.noResultsTitle'), <>{t('list.noResultsBody')} “<span className="font-medium text-foreground break-all">{q.trim()}</span>”. <Button size="sm" variant="outline" className="ml-2" onClick={() => setQ('')}>{t('list.clearSearch')}</Button></>, 'wf-no-results')}
          </TableBody>
        </Table>
      </Card>
    </main>
    <Dialog open={!!rename} onOpenChange={o => !o && setRename(null)}>
      <DialogContent><DialogHeader><DialogTitle>{t('list.renameTitle')}</DialogTitle></DialogHeader>
        <div className="space-y-1.5">
          <Input id="rename-input" aria-label={t('list.renameLabel')} maxLength={120} value={newName} aria-invalid={!trimmed || !!renameErr} onChange={e => { setNewName(e.target.value); setRenameErr('') }} onKeyDown={e => e.key === 'Enter' && doRename()} />
          <div className="flex justify-between text-xs"><span className="text-destructive" role="alert" id="rename-error">{!trimmed ? t('list.nameRequired') : renameErr}</span><span className="text-muted-foreground">{trimmed.length}/120</span></div>
        </div>
        <DialogFooter><Button variant="outline" onClick={() => setRename(null)}>{t('common.cancel')}</Button><Button id="rename-save" onClick={doRename} disabled={!trimmed || busy}>{busy && <Loader2 className="animate-spin" />}{t('common.save')}</Button></DialogFooter></DialogContent>
    </Dialog>
    {confirmDel.dialog}
    {creates && <TemplateGallery open={gallery} onOpenChange={setGallery} onBlank={create} />}
  </div>
}
