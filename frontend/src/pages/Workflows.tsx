import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Workflow, Plus, Search, Copy, Pencil, Trash2, MoreHorizontal } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Card } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator, DropdownMenuTrigger } from '@/components/ui/dropdown-menu'
import { api } from '@/lib/api'
import { ThemeToggle } from '@/lib/theme'
import { UserMenu } from '@/components/user-menu'
import { ImportDialog } from '@/components/import-dialog'
import { CredentialsDialog } from '@/components/credentials-dialog'

type W = { id: string; name: string; updated: number; node_count: number; last_run_status: string | null; last_run_at: number | null }
const fmt = (t: number) => new Date(t * 1000).toLocaleString('vi-VN')

export function WorkflowsPage() {
  const nav = useNavigate()
  const [items, setItems] = useState<W[]>([]); const [q, setQ] = useState('')
  const [rename, setRename] = useState<W | null>(null); const [newName, setNewName] = useState('')
  const [del, setDel] = useState<W | null>(null)
  const load = () => api<W[]>('/api/workflows').then(setItems)
  useEffect(() => { load() }, [])
  const create = async () => {
    const r = await api('/api/workflows', { method: 'POST', json: { name: 'Untitled workflow', state: [{ name: 'message', type: 'string' }],
      nodes: [{ id: 'start', type: 'start', position: { x: 80, y: 200 }, data: { label: 'Start' } }, { id: 'end', type: 'end', position: { x: 480, y: 200 }, data: { label: 'End' } }],
      edges: [{ id: 'e1', source: 'start', target: 'end' }] } })
    nav(`/workflows/${r.id}`)
  }
  const dup = async (w: W) => { await api(`/api/workflows/${w.id}/duplicate`, { method: 'POST' }); load() }
  const doRename = async () => { if (!rename) return; await api(`/api/workflows/${rename.id}`, { method: 'PATCH', json: { name: newName } }); setRename(null); load() }
  const doDelete = async () => { if (!del) return; await api(`/api/workflows/${del.id}`, { method: 'DELETE' }); setDel(null); load() }
  const shown = items.filter(w => w.name.toLowerCase().includes(q.toLowerCase()))

  return <div className="min-h-screen bg-background text-foreground">
    <header className="h-14 border-b flex items-center gap-3 px-6">
      <div className="flex items-center gap-2 font-semibold"><div className="rounded-md bg-primary text-primary-foreground p-1.5"><Workflow className="size-4" /></div>LangGraph Studio</div>
      <div className="ml-auto flex items-center gap-1"><ThemeToggle /><UserMenu /></div>
    </header>
    <main className="max-w-6xl mx-auto p-6 space-y-4">
      <div className="flex items-end justify-between gap-4">
        <div><h1 className="text-2xl font-semibold tracking-tight">Workflows</h1><p className="text-sm text-muted-foreground">{items.length} workflow của bạn</p></div>
        <div className="flex gap-2">
          <div className="relative"><Search className="absolute left-2.5 top-2.5 size-4 text-muted-foreground" /><Input className="pl-8 w-64" placeholder="Tìm workflow…" value={q} onChange={e => setQ(e.target.value)} /></div>
          <CredentialsDialog />
          <ImportDialog />
          <Button onClick={create} id="new-wf"><Plus />New workflow</Button>
        </div>
      </div>
      <Card className="p-0 overflow-hidden">
        <Table>
          <TableHeader><TableRow><TableHead className="pl-4">Tên</TableHead><TableHead>Nodes</TableHead><TableHead>Cập nhật</TableHead><TableHead>Lần chạy cuối</TableHead><TableHead className="w-12" /></TableRow></TableHeader>
          <TableBody>
            {shown.map(w => <TableRow key={w.id} className="cursor-pointer" onClick={() => nav(`/workflows/${w.id}`)}>
              <TableCell className="pl-4 font-medium">{w.name}<div className="text-xs text-muted-foreground font-mono">{w.id}</div></TableCell>
              <TableCell><Badge variant="secondary">{w.node_count}</Badge></TableCell>
              <TableCell className="text-muted-foreground">{fmt(w.updated)}</TableCell>
              <TableCell>{w.last_run_status ? <div className="flex items-center gap-2">
                <Badge className={w.last_run_status === 'ok' ? 'bg-emerald-600 text-white' : ''} variant={w.last_run_status === 'ok' ? 'default' : 'destructive'}>{w.last_run_status}</Badge>
                <span className="text-xs text-muted-foreground">{fmt(w.last_run_at!)}</span></div> : <span className="text-xs text-muted-foreground">Chưa chạy</span>}</TableCell>
              <TableCell onClick={e => e.stopPropagation()}>
                <DropdownMenu><DropdownMenuTrigger asChild><Button variant="ghost" size="icon"><MoreHorizontal /></Button></DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuItem onClick={() => { setRename(w); setNewName(w.name) }}><Pencil />Đổi tên</DropdownMenuItem>
                    <DropdownMenuItem onClick={() => dup(w)}><Copy />Nhân bản</DropdownMenuItem>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem variant="destructive" onClick={() => setDel(w)}><Trash2 />Xoá</DropdownMenuItem>
                  </DropdownMenuContent></DropdownMenu>
              </TableCell>
            </TableRow>)}
            {!shown.length && <TableRow><TableCell colSpan={5} className="text-center text-muted-foreground py-10">Không có workflow nào.</TableCell></TableRow>}
          </TableBody>
        </Table>
      </Card>
    </main>
    <Dialog open={!!rename} onOpenChange={o => !o && setRename(null)}>
      <DialogContent><DialogHeader><DialogTitle>Đổi tên workflow</DialogTitle></DialogHeader>
        <Input value={newName} onChange={e => setNewName(e.target.value)} onKeyDown={e => e.key === 'Enter' && doRename()} />
        <DialogFooter><Button variant="outline" onClick={() => setRename(null)}>Huỷ</Button><Button onClick={doRename} disabled={!newName.trim()}>Lưu</Button></DialogFooter></DialogContent>
    </Dialog>
    <Dialog open={!!del} onOpenChange={o => !o && setDel(null)}>
      <DialogContent><DialogHeader><DialogTitle>Xoá workflow?</DialogTitle><DialogDescription>“{del?.name}” và toàn bộ lịch sử chạy sẽ bị xoá vĩnh viễn.</DialogDescription></DialogHeader>
        <DialogFooter><Button variant="outline" onClick={() => setDel(null)}>Huỷ</Button><Button variant="destructive" onClick={doDelete}>Xoá</Button></DialogFooter></DialogContent>
    </Dialog>
  </div>
}
