import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { GitFork, Upload, Loader2, AlertCircle, CheckCircle2, ShieldAlert } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { api } from '@/lib/api'
import { cn } from '@/lib/utils'

type Job = { id: string; status: string; log: string[]; error: string | null; graphs: { id: string; ref: string; via: string; name: string; nodes: number; edges: number }[]; required_env: string[] }
const STEPS = ['fetching', 'installing', 'inspecting', 'ready']

export function ImportDialog() {
  const nav = useNavigate()
  const [open, setOpen] = useState(false); const [tab, setTab] = useState('url')
  const [url, setUrl] = useState('https://github.com/langchain-ai/react-agent'); const [branch, setBranch] = useState(''); const [subdir, setSubdir] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [job, setJob] = useState<Job | null>(null); const [err, setErr] = useState(''); const [pick, setPick] = useState('')
  const timer = useRef<number | undefined>(undefined)
  useEffect(() => () => clearInterval(timer.current), [])
  const busy = !!job && !['ready', 'error'].includes(job.status)

  const start = async () => {
    setErr(''); setJob(null); setPick('')
    const fd = new FormData()
    if (tab === 'url') { fd.append('url', url); if (branch) fd.append('branch', branch) } else if (file) fd.append('file', file); else { setErr('Chọn file zip'); return }
    if (subdir) fd.append('subdir', subdir)
    try {
      const r = await api('/api/import', { method: 'POST', body: fd })
      setJob({ id: r.job_id, status: 'queued', log: [], error: null, graphs: [], required_env: [] })
      clearInterval(timer.current)
      timer.current = window.setInterval(async () => {
        const j: Job = await api(`/api/import/${r.job_id}`); setJob(j)
        if (j.status === 'ready' || j.status === 'error') { clearInterval(timer.current); if (j.graphs[0]) setPick(j.graphs[0].id); if (j.error) setErr(j.error) }
      }, 800)
    } catch (e: any) { setErr(e.message) }
  }
  const finalize = async () => {
    try { const r = await api(`/api/import/${job!.id}/finalize`, { method: 'POST', json: { graph_id: pick } }); setOpen(false); nav(`/workflows/${r.id}`) }
    catch (e: any) { setErr(e.message) }
  }

  return <Dialog open={open} onOpenChange={setOpen}>
    <DialogTrigger asChild><Button variant="outline" id="import-btn"><GitFork />Import repo</Button></DialogTrigger>
    <DialogContent className="sm:max-w-2xl">
      <DialogHeader><DialogTitle>Import LangGraph repo</DialogTitle>
        <DialogDescription>Clone repo, cài dependencies vào venv riêng, đọc graph từ <code>langgraph.json</code> (hoặc quét StateGraph đã compile).</DialogDescription></DialogHeader>
      <div className="flex items-start gap-2 rounded-md border border-amber-500/40 bg-amber-500/10 px-3 py-2 text-xs text-amber-700 dark:text-amber-300">
        <ShieldAlert className="size-4 shrink-0" />Code của repo sẽ được thực thi (trong subprocess + venv riêng, không phải sandbox đầy đủ). Chỉ import repo bạn tin tưởng.</div>
      <Tabs value={tab} onValueChange={setTab}>
        <TabsList><TabsTrigger value="url"><GitFork />GitHub URL</TabsTrigger><TabsTrigger value="zip"><Upload />Zip upload</TabsTrigger></TabsList>
        <TabsContent value="url" className="space-y-3 pt-2">
          <div className="space-y-1.5"><Label>Repo URL (public)</Label><Input id="import-url" value={url} onChange={e => setUrl(e.target.value)} placeholder="https://github.com/owner/repo" /></div>
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5"><Label>Branch (tuỳ chọn)</Label><Input value={branch} onChange={e => setBranch(e.target.value)} placeholder="main" /></div>
            <div className="space-y-1.5"><Label>Subdir (tuỳ chọn)</Label><Input value={subdir} onChange={e => setSubdir(e.target.value)} placeholder="examples/agent" /></div>
          </div>
        </TabsContent>
        <TabsContent value="zip" className="space-y-3 pt-2">
          <div className="space-y-1.5"><Label>File .zip</Label><Input type="file" accept=".zip" onChange={e => setFile(e.target.files?.[0] || null)} /></div>
          <div className="space-y-1.5"><Label>Subdir (tuỳ chọn)</Label><Input value={subdir} onChange={e => setSubdir(e.target.value)} /></div>
        </TabsContent>
      </Tabs>
      {job && <div className="space-y-2">
        <div className="flex items-center gap-2 text-xs">{STEPS.map((s, i) => { const cur = STEPS.indexOf(job.status); const done = cur > i || job.status === 'ready'
          return <div key={s} className="flex items-center gap-1.5">
            <Badge variant={done ? 'default' : 'outline'} className={cn(done && 'bg-emerald-600 text-white', cur === i && job.status !== 'ready' && 'border-amber-500')}>
              {cur === i && busy ? <Loader2 className="size-3 animate-spin" /> : done ? <CheckCircle2 className="size-3" /> : null}{s}</Badge>{i < 3 && <span className="text-muted-foreground">→</span>}</div> })}
          {job.status === 'error' && <Badge variant="destructive">error</Badge>}</div>
        <ScrollArea className="h-40 rounded-md border bg-muted/40"><pre className="p-2 text-[11px] whitespace-pre-wrap">{job.log.join('\n') || 'Đang chờ…'}</pre></ScrollArea>
      </div>}
      {err && <div className="flex items-center gap-2 rounded-md border border-destructive/50 bg-destructive/10 px-3 py-2 text-sm text-destructive" role="alert"><AlertCircle className="size-4" />{err}</div>}
      {job?.status === 'ready' && <div className="space-y-2">
        <Label>Chọn graph ({job.graphs.length})</Label>
        {job.graphs.map(g => <button key={g.id} onClick={() => setPick(g.id)} className={cn('w-full text-left rounded-md border px-3 py-2 text-sm hover:bg-accent', pick === g.id && 'border-primary ring-1 ring-primary')}>
          <div className="font-medium">{g.id} <span className="text-muted-foreground font-normal">· {g.name}</span></div>
          <div className="text-xs text-muted-foreground font-mono">{g.ref} · {g.nodes} nodes · {g.edges} edges · via {g.via}</div></button>)}
        {job.required_env.length > 0 && <p className="text-xs text-muted-foreground">Repo khai báo biến môi trường: {job.required_env.map(k => <Badge key={k} variant="outline" className="mr-1">{k}</Badge>)} — cần đặt trong env server để chạy.</p>}
      </div>}
      <DialogFooter>
        <Button variant="outline" onClick={() => setOpen(false)}>Đóng</Button>
        {job?.status === 'ready' ? <Button onClick={finalize} disabled={!pick} id="import-create">Tạo workflow</Button>
          : <Button onClick={start} disabled={busy} id="import-start">{busy && <Loader2 className="animate-spin" />}Import</Button>}
      </DialogFooter>
    </DialogContent>
  </Dialog>
}
