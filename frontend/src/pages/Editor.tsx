import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import {
  ReactFlow, ReactFlowProvider, Background, Controls, MiniMap, Handle, Position, addEdge,
  useNodesState, useEdgesState, useReactFlow, type Node, type Edge, type Connection, type NodeProps,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import { Play, Save, Brain, Wrench, GitBranch, Flag, CirclePlay, Plus, Trash2, Braces, Workflow, Loader2, CheckCircle2, XCircle, Code2, Sparkles, GitFork, type LucideIcon } from 'lucide-react'
import dagre from '@dagrejs/dagre'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Card } from '@/components/ui/card'
import { Separator } from '@/components/ui/separator'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogDescription } from '@/components/ui/dialog'
import { cn } from '@/lib/utils'
import { useParams, Link } from 'react-router-dom'
import { ArrowLeft, Square, AlertTriangle } from 'lucide-react'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { api, wsUrl, sessionExpired, tokenValid } from '@/lib/api'
import { useTheme, ThemeToggle } from '@/lib/theme'
import { UserMenu } from '@/components/user-menu'
import type { Credential } from '@/components/credentials-dialog'
import { RunTrace } from '@/components/run-trace'
import { buildTrace } from '@/lib/trace'

type Field = { name: string; type: string }
type LogItem = { type: string; node?: string; label?: string; duration_ms?: number; delta?: any; state?: any; errors?: string[] }
const META: Record<string, { label: string; icon: LucideIcon; color: string; accent: string; desc: string }> = {
  start: { label: 'Start', icon: CirclePlay, color: 'bg-node-start-muted text-node-start', accent: 'bg-node-start', desc: 'Điểm bắt đầu' },
  llm: { label: 'LLM', icon: Brain, color: 'bg-node-llm-muted text-node-llm', accent: 'bg-node-llm', desc: 'Gọi model với prompt' },
  tool: { label: 'Tool/API', icon: Wrench, color: 'bg-node-tool-muted text-node-tool', accent: 'bg-node-tool', desc: 'HTTP hoặc Python function' },
  condition: { label: 'Condition', icon: GitBranch, color: 'bg-node-condition-muted text-node-condition', accent: 'bg-node-condition', desc: 'Rẽ nhánh theo state field' },
  end: { label: 'End', icon: Flag, color: 'bg-node-end-muted text-node-end', accent: 'bg-node-end', desc: 'Kết thúc' },
}
META.code = { label: 'Code', icon: Code2, color: 'bg-node-code-muted text-node-code', accent: 'bg-node-code', desc: 'Node Python từ repo import' }
const TYPES = ['start', 'llm', 'tool', 'condition', 'end']

function autoLayout(nodes: Node[], edges: Edge[]): Node[] {
  const g = new dagre.graphlib.Graph(); g.setGraph({ rankdir: 'LR', nodesep: 60, ranksep: 110 }); g.setDefaultEdgeLabel(() => ({}))
  nodes.forEach(n => g.setNode(n.id, { width: 200, height: 70 })); edges.forEach(e => g.setEdge(e.source, e.target))
  dagre.layout(g)
  return nodes.map(n => { const p = g.node(n.id); return { ...n, position: { x: p.x - 100, y: p.y - 35 } } })
}
const styleEdges = (es: any[]): Edge[] => es.map(e => e.conditional ? { ...e, animated: true, style: { strokeDasharray: '6 4' }, labelBgPadding: [6, 3], labelBgBorderRadius: 4 } : e)
function defaultInput(state: Field[]) {
  return JSON.stringify(Object.fromEntries(state.map(f => [f.name, f.type === 'list' ? [{ role: 'user', content: 'Xin chào!' }] : f.type === 'number' || f.type === 'integer' ? 0 : f.type === 'boolean' ? false : f.type === 'object' ? {} : 'hello'])), null, 2)
}
const DEFAULTS: Record<string, any> = {
  start: { label: 'Start' }, end: { label: 'End' },
  llm: { label: 'LLM', model: 'gpt-4o-mini', prompt: 'Trả lời: {{state.message}}', output_field: '' },
  tool: { label: 'Tool', mode: 'function', function: 'lookup_order', method: 'GET', url: '', body: '', output_field: '' },
  condition: { label: 'Condition', field: '', default: '' },
}

function StatusBadge({ s }: { s?: string }) {
  if (s === 'running') return <Badge variant="warning" className="gap-1"><Loader2 className="size-3 animate-spin" />running</Badge>
  if (s === 'done') return <Badge variant="success" className="gap-1"><CheckCircle2 className="size-3" />done</Badge>
  if (s === 'error') return <Badge variant="destructive" className="gap-1"><XCircle className="size-3" />error</Badge>
  if (s === 'cancelled') return <Badge variant="secondary" className="gap-1"><Square className="size-3" />cancelled</Badge>
  return null
}

function StudioNode({ data, type, selected }: NodeProps) {
  const d = data as any; const m = META[type!]; const I = m.icon
  return <div className={cn(type === 'code' && 'border-node-code/60 border-dashed', 'relative rounded-xl border bg-card text-card-foreground shadow-sm px-3 py-2 min-w-44 transition-all',
    selected && 'ring-2 ring-ring', d._hl && 'ring-4 ring-primary/40 shadow-md', d._status === 'running' && 'border-warning ring-4 ring-warning/30',
    d._status === 'done' && 'border-success', d._status === 'error' && 'border-destructive')}>
    <span aria-hidden className={cn('absolute inset-y-0 left-0 w-1 rounded-l-xl', m.accent)} />
    {type !== 'start' && <Handle type="target" position={Position.Left} />}
    <div className="flex items-center gap-2">
      <div className={cn('rounded-md p-1.5', m.color)}><I className="size-4" /></div>
      <div className="flex-1 min-w-0">
        <div className="text-[10px] uppercase tracking-wide text-muted-foreground">{m.label}</div>
        <div className="text-sm font-medium truncate ">{d.label}</div>
        {type === 'code' && <div className="flex gap-1 mt-0.5">{d.is_llm && <Badge variant="outline" className="h-4 px-1 text-[9px] gap-0.5"><Sparkles className="size-2.5" />LLM</Badge>}{d.kind && <span className="text-[9px] text-muted-foreground font-mono">{d.kind}</span>}</div>}
      </div>
    </div>
    {(d._status || d._dur != null) && <div className="mt-2 flex items-center justify-between gap-2">
      <StatusBadge s={d._status} />{d._dur != null && <span className="text-[10px] text-muted-foreground">{d._dur} ms</span>}</div>}
    {type !== 'end' && <Handle type="source" position={Position.Right} />}
  </div>
}
const nodeTypes = Object.fromEntries([...TYPES, 'code'].map(t => [t, StudioNode]))

function Tip({ tip, children }: { tip: string; children: React.ReactElement }) {
  return <Tooltip><TooltipTrigger asChild>{children}</TooltipTrigger><TooltipContent>{tip}</TooltipContent></Tooltip>
}

const Sel = ({ value, onChange, opts, ph }: { value?: string; onChange: (v: string) => void; opts: string[]; ph?: string }) =>
    <Select value={value || undefined} onValueChange={onChange}>
      <SelectTrigger className="w-full"><SelectValue placeholder={ph || 'Chọn…'} /></SelectTrigger>
      <SelectContent>{opts.filter(Boolean).map(o => <SelectItem key={o} value={o}>{o}</SelectItem>)}</SelectContent>
    </Select>
const F = ({ label, children }: { label: string; children: React.ReactNode }) => <div className="space-y-1.5"><Label className="text-xs text-muted-foreground">{label}</Label>{children}</div>

export function EditorPage() { return <ReactFlowProvider><Studio /></ReactFlowProvider> }

function Studio() {
  const { id } = useParams()
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([])
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([])
  const [state, setState] = useState<Field[]>([])
  const [name, setName] = useState('Untitled')
  const [wid, setWid] = useState<string | undefined>()
  const [sel, setSel] = useState<{ kind: 'node' | 'edge'; id: string } | null>(null)
  const [input, setInput] = useState('{\n  "message": "Đơn hàng A100 của tôi đâu rồi?"\n}')
  const [log, setLog] = useState<LogItem[]>([])
  const [errors, setErrors] = useState<string[]>([])
  const [tools, setTools] = useState<{ name: string }[]>([])
  const [mode, setMode] = useState('')
  const [source, setSource] = useState<any>(null)
  const [creds, setCreds] = useState<Credential[]>([])
  const [history, setHistory] = useState<any[]>([])
  const [tab, setTab] = useState('input')
  const [running, setRunning] = useState(false)
  const [traceSel, setTraceSel] = useState<string | null>(null); const [replay, setReplay] = useState<string | null>(null)
  const [loadErr, setLoadErr] = useState<{ status: number; msg: string } | null>(null)
  const { dark } = useTheme()
  const rf = useReactFlow(); const idc = useRef(1); const wsRef = useRef<WebSocket | null>(null)

  const load = (wf: any) => {
    setName(wf.name); setWid(wf.id); setState(wf.state || [])
    setSource(wf.source || null)
    setNodes(wf.needs_layout ? autoLayout(wf.nodes, wf.edges) : wf.nodes); setEdges(styleEdges(wf.edges))
    if (wf.source) setInput(defaultInput(wf.state || []))
  }
  const loadHistory = (id?: string) => id && api(`/api/workflows/${id}/runs`).then(setHistory)
  useEffect(() => {
    api(`/api/workflows/${id}`).then(wf => { setLoadErr(null); load(wf); loadHistory(wf.id) }).catch(e => setLoadErr({ status: e.status ?? 0, msg: e.message }))
    api('/api/tools').then(setTools).catch(() => {})
    api<Credential[]>('/api/credentials').then(setCreds).catch(() => {})
    fetch('/api/health').then(r => r.json()).then(h => setMode(h.llm_mode)).catch(() => {})
  }, [id])

  const toJSON = () => ({
    id: wid, name, state,
    nodes: nodes.map(n => ({ id: n.id, type: n.type, position: n.position, data: Object.fromEntries(Object.entries(n.data).filter(([k]) => !k.startsWith('_'))) })),
    edges: edges.map(e => ({ id: e.id, source: e.source, target: e.target, ...(e.label ? { label: String(e.label) } : {}), ...((e as any).conditional ? { conditional: true } : {}) })),
  })
  const save = async () => {
    try {
      const r = await api('/api/workflows', { method: 'POST', json: toJSON() })
      setWid(r.id); setErrors(r.errors); if (r.errors.length) setTab('input')
    } catch (e: any) { setErrors([`Lưu thất bại: ${e.message}`]); setTab('input') }
  }
  const mark = (id: string, patch: any) => setNodes(ns => ns.map(n => n.id === id ? { ...n, data: { ...n.data, ...patch } } : n))
  const run = () => {
    let inp: any; try { inp = JSON.parse(input) } catch { setErrors(['Input không phải JSON hợp lệ']); setTab('input'); return }
    if (!tokenValid()) { setErrors(['Phiên đăng nhập đã hết hạn. Đang chuyển tới trang đăng nhập…']); setTab('logs'); setTimeout(sessionExpired, 1500); return }
    setLog([]); setErrors([]); setTab('logs'); setRunning(true); setReplay(null); setTraceSel(null)
    setNodes(ns => ns.map(n => ({ ...n, data: { ...n.data, _status: '', _dur: null } })))
    const ws = new WebSocket(wsUrl('/ws/run')); wsRef.current = ws
    ws.onopen = () => ws.send(JSON.stringify({ workflow_id: wid, workflow: toJSON(), input: inp }))
    ws.onmessage = m => {
      const ev: LogItem = JSON.parse(m.data); setLog(l => [...l, ev])
      if (ev.type === 'node_started') mark(ev.node!, { _status: 'running' })
      if (ev.type === 'node_finished') mark(ev.node!, { _status: 'done', _dur: ev.duration_ms })
      if (ev.type === 'error') { setErrors(ev.errors || []); if (ev.node) mark(ev.node, { _status: 'error' }) }
      if (ev.type === 'run_cancelled' || (ev.type === 'error' && (ev as any).status === 'timeout')) setNodes(ns => ns.map(n => n.data._status === 'running' ? { ...n, data: { ...n.data, _status: 'cancelled' } } : n))
    }
    ws.onerror = () => setErrors(e => e.length ? e : ['Mất kết nối tới máy chủ khi đang chạy'])
    ws.onclose = ev => {
      if (ev.code === 4401) { setErrors(['Phiên đăng nhập đã hết hạn trong khi chạy. Đang chuyển tới trang đăng nhập…']); setTimeout(sessionExpired, 1500) }
      setRunning(false); setNodes(ns => ns.map(n => n.data._status === 'running' ? { ...n, data: { ...n.data, _status: 'error' } } : n)); loadHistory(wid) }
  }

  const trace = useMemo(() => buildTrace(log as any, nid => { const n = nodes.find(x => x.id === nid); return { label: (n?.data as any)?.label, type: n?.type } }), [log, nodes])
  const traceMeta = (t: string) => META[t] || META.code
  const hlNode = traceSel ? trace.spans.find(x => x.key === traceSel)?.node : undefined
  const nodesView = useMemo(() => hlNode ? nodes.map(n => n.id === hlNode ? { ...n, data: { ...n.data, _hl: true } } : n) : nodes, [nodes, hlNode])
  const onNodeClick = (id: string) => {
    setSel({ kind: 'node', id })
    const spans = trace.spans.filter(x => x.node === id)
    if (spans.length) {
      const cur = spans.findIndex(x => x.key === traceSel) // repeated clicks cycle through loop iterations
      setTraceSel(spans[cur >= 0 ? (cur + 1) % spans.length : spans.length - 1].key); setTab('logs')
    }
  }
  const onConnect = useCallback((c: Connection) => setEdges(es => addEdge({ ...c, id: 'e' + Date.now() }, es)), [])
  const onDrop = (ev: React.DragEvent) => {
    ev.preventDefault(); const t = ev.dataTransfer.getData('nodetype'); if (!t) return
    const pos = rf.screenToFlowPosition({ x: ev.clientX, y: ev.clientY })
    setNodes(ns => [...ns, { id: `${t}_${Date.now().toString(36)}${idc.current++}`, type: t, position: pos, data: { ...DEFAULTS[t] } }])
  }
  const selNode = sel?.kind === 'node' ? nodes.find(n => n.id === sel.id) : undefined
  const selEdge = sel?.kind === 'edge' ? edges.find(e => e.id === sel.id) : undefined
  const upd = (k: string, v: any) => selNode && mark(selNode.id, { [k]: v })
  const d: any = selNode?.data || {}
  const fieldNames = state.map(f => f.name)

  if (loadErr) return <div className="min-h-screen flex items-center justify-center bg-muted/40 p-4 text-foreground">
    <div className="max-w-sm text-center space-y-3 rounded-xl border bg-card p-8 shadow-sm" id="editor-not-found">
      <div className="mx-auto w-fit rounded-full bg-muted p-3 text-muted-foreground"><ArrowLeft className="size-5" /></div>
      <h1 className="text-lg font-semibold">{loadErr.status === 404 ? 'Không tìm thấy workflow' : 'Không mở được workflow'}</h1>
      <p className="text-sm text-muted-foreground">{loadErr.status === 404 ? 'Workflow này đã bị xoá hoặc không thuộc tài khoản của bạn.' : loadErr.msg}</p>
      <Button asChild><Link to="/workflows" id="back-to-list">Về danh sách workflow</Link></Button>
    </div>
  </div>

  return <div className="h-screen grid grid-rows-[56px_1fr_300px] grid-cols-[250px_1fr_320px] bg-background text-foreground text-sm">
    {/* Top bar */}
    <header className="col-span-3 flex items-center gap-3 border-b px-4">
      <Tip tip="Về danh sách workflow"><Button variant="ghost" size="icon" asChild><Link to="/workflows" id="back-btn"><ArrowLeft /></Link></Button></Tip>
      <div className="flex items-center gap-2 font-semibold"><div className="rounded-md bg-primary text-primary-foreground p-1.5"><Workflow className="size-4" /></div>LangGraph Studio</div>
      <Separator orientation="vertical" className="h-6!" />
      <Input value={name} onChange={e => setName(e.target.value)} className="w-72 h-8" />
      <Tip tip="Lưu workflow (SQLite)"><Button variant="outline" size="sm" onClick={save}><Save />Save</Button></Tip>
      <Tip tip="Chạy workflow với input hiện tại"><Button size="sm" id="run-btn" onClick={run} disabled={running}>{running ? <Loader2 className="animate-spin" /> : <Play />}Run</Button></Tip>
      {running && <Tip tip="Dừng run (huỷ giữa các bước)"><Button size="sm" variant="outline" id="cancel-btn" onClick={() => wsRef.current?.readyState === WebSocket.OPEN && wsRef.current.send(JSON.stringify({ type: 'cancel' }))}><Square />Cancel</Button></Tip>}
      <Dialog>
        <Tip tip="Xem JSON"><DialogTrigger asChild><Button variant="ghost" size="sm"><Braces />JSON</Button></DialogTrigger></Tip>
        <DialogContent className="sm:max-w-2xl"><DialogHeader><DialogTitle>Workflow JSON</DialogTitle><DialogDescription>Định dạng gửi lên backend.</DialogDescription></DialogHeader>
          <ScrollArea className="h-96 rounded-md border bg-muted/40"><pre className="p-3 text-xs">{JSON.stringify(toJSON(), null, 2)}</pre></ScrollArea>
        </DialogContent>
      </Dialog>
      <div className="ml-auto flex items-center gap-2">
        {source && <Tip tip={`Chạy code gốc trong venv riêng (subprocess). ${source.repo_url || 'zip'} · ${source.ref}`}><Badge variant="secondary" className="gap-1"><GitFork className="size-3" />Imported repo</Badge></Tip>}
        <Badge variant="secondary">LLM: {mode}</Badge>{wid && <Badge variant="outline">id: {wid}</Badge>}
        <ThemeToggle /><UserMenu />
      </div>
    </header>

    {/* Left */}
    <aside className="border-r bg-muted/30 min-h-0">
      <ScrollArea className="h-full"><div className="p-3 space-y-4">
        <div>
          <div className="text-xs font-semibold uppercase text-muted-foreground mb-2">Node palette</div>
          <div className="space-y-2">{TYPES.map(t => { const m = META[t]; const I = m.icon
            return <Card key={t} draggable onDragStart={e => { e.dataTransfer.setData('nodetype', t); e.dataTransfer.effectAllowed = 'move' }}
              className="flex-row items-center gap-3 p-2.5 cursor-grab hover:bg-accent transition-colors py-2.5">
              <div className={cn('rounded-md p-1.5', m.color)}><I className="size-4" /></div>
              <div><div className="font-medium leading-tight">{m.label}</div><div className="text-[11px] text-muted-foreground">{m.desc}</div></div>
            </Card> })}</div>
        </div>
        <Separator />
        <div>
          <div className="text-xs font-semibold uppercase text-muted-foreground mb-2">State schema</div>
          <div className="space-y-1.5">{state.map((f, i) => <div className="flex gap-1" key={i}>
            <Input className="h-8 flex-1 min-w-0" value={f.name} onChange={e => setState(s => s.map((x, j) => j === i ? { ...x, name: e.target.value } : x))} />
            <Select value={f.type} onValueChange={v => setState(s => s.map((x, j) => j === i ? { ...x, type: v } : x))}>
              <SelectTrigger size="sm" className="w-24"><SelectValue /></SelectTrigger>
              <SelectContent>{['string', 'number', 'integer', 'boolean', 'object', 'list'].map(t => <SelectItem key={t} value={t}>{t}</SelectItem>)}</SelectContent>
            </Select>
            <Button variant="ghost" size="icon" className="size-8" onClick={() => setState(s => s.filter((_, j) => j !== i))}><Trash2 /></Button>
          </div>)}</div>
          <Button variant="outline" size="sm" className="mt-2 w-full" onClick={() => setState(s => [...s, { name: 'field' + (s.length + 1), type: 'string' }])}><Plus />Thêm field</Button>
        </div>
      </div></ScrollArea>
    </aside>

    {/* Canvas */}
    <main className="min-h-0" onDrop={onDrop} onDragOver={e => { e.preventDefault(); e.dataTransfer.dropEffect = 'move' }}>
      <ReactFlow nodes={nodesView} edges={edges} nodeTypes={nodeTypes} onNodesChange={onNodesChange} onEdgesChange={onEdgesChange}
        colorMode={dark ? 'dark' : 'light'} onConnect={onConnect} onNodeClick={(_, n) => onNodeClick(n.id)}
        onEdgeClick={(_, e) => setSel({ kind: 'edge', id: e.id })} onPaneClick={() => setSel(null)} deleteKeyCode={['Delete', 'Backspace']} fitView>
        <Background /><Controls /><MiniMap pannable zoomable />
      </ReactFlow>
    </main>

    {/* Right config */}
    <aside className="border-l bg-muted/30 min-h-0">
      <ScrollArea className="h-full"><div className="p-4 space-y-4 w-[318px]">
        <div className="text-xs font-semibold uppercase text-muted-foreground">Config</div>
        {!selNode && !selEdge && <p className="text-muted-foreground text-xs">Chọn một node hoặc edge để cấu hình. Nhấn Delete để xoá.</p>}
        {selEdge && <div className="space-y-3">
          <Badge variant="outline">Edge {selEdge.source} → {selEdge.target}</Badge>
          <F label="Label (khớp với giá trị field của Condition)"><Input value={String(selEdge.label || '')} onChange={e => setEdges(es => es.map(x => x.id === selEdge.id ? { ...x, label: e.target.value } : x))} /></F>
          <Button variant="destructive" size="sm" onClick={() => { setEdges(es => es.filter(x => x.id !== selEdge.id)); setSel(null) }}><Trash2 />Xoá edge</Button>
        </div>}
        {selNode && <div className="space-y-3">
          <div className="flex items-center gap-2">{(() => { const m = META[selNode.type!]; const I = m.icon; return <div className={cn('rounded-md p-1.5', m.color)}><I className="size-4" /></div> })()}
            <div><div className="font-medium">{META[selNode.type!].label}</div><div className="text-[11px] text-muted-foreground font-mono">{selNode.id}</div></div></div>
          <F label="Label"><Input value={d.label || ''} onChange={e => upd('label', e.target.value)} /></F>
          {selNode.type === 'llm' && <>
            <F label="Credential (provider)"><Select value={d.credential_id || 'none'} onValueChange={v => upd('credential_id', v === 'none' ? '' : v)}>
              <SelectTrigger className="w-full" id="llm-credential"><SelectValue /></SelectTrigger>
              <SelectContent><SelectItem value="none">Mặc định (env OPENAI_API_KEY hoặc mock)</SelectItem>
                {creds.map(c => <SelectItem key={c.id} value={c.id}>{c.name} · {c.provider} {c.hint}</SelectItem>)}</SelectContent></Select></F>
            <F label="Model"><Input value={d.model} onChange={e => upd('model', e.target.value)} placeholder={creds.find(c => c.id === d.credential_id)?.provider === 'anthropic' ? 'claude-3-5-haiku-latest' : 'gpt-4o-mini'} /></F>
            <F label="Prompt template ({{state.field}})"><Textarea rows={7} className="font-mono text-xs" value={d.prompt} onChange={e => upd('prompt', e.target.value)} /></F>
            <F label="Output field"><Sel value={d.output_field} onChange={v => upd('output_field', v)} opts={fieldNames} /></F>
          </>}
          {selNode.type === 'tool' && <>
            <F label="Mode"><Select value={d.mode} onValueChange={v => upd('mode', v)}><SelectTrigger className="w-full"><SelectValue /></SelectTrigger>
              <SelectContent><SelectItem value="function">Python function</SelectItem><SelectItem value="http">HTTP request</SelectItem></SelectContent></Select></F>
            {d.mode === 'http' ? <>
              <F label="Method"><Sel value={d.method} onChange={v => upd('method', v)} opts={['GET', 'POST', 'PUT', 'DELETE']} /></F>
              <F label="URL"><Input value={d.url} onChange={e => upd('url', e.target.value)} placeholder="https://…" /></F>
              <F label="Body template"><Textarea rows={4} className="font-mono text-xs" value={d.body} onChange={e => upd('body', e.target.value)} /></F>
            </> : <F label="Function"><Sel value={d.function} onChange={v => upd('function', v)} opts={tools.map(t => t.name)} /></F>}
            <F label="Output field"><Sel value={d.output_field} onChange={v => upd('output_field', v)} opts={fieldNames} /></F>
          </>}
          {selNode.type === 'code' && <>
            <div className="flex flex-wrap gap-1 max-w-[286px]">{d.is_llm && <Badge variant="outline" className="gap-1"><Sparkles className="size-3" />Có vẻ là LLM call</Badge>}{d.kind && <Badge variant="secondary">{d.kind}</Badge>}<Badge variant="outline">read-only</Badge></div>
            <F label="Node name"><Input readOnly value={d.node_name || ''} className="font-mono text-xs" /></F>
            <F label="Reference (module:function)"><Input readOnly value={d.ref || ''} className="font-mono text-xs" /></F>
            <F label="Source"><pre className="h-72 w-[286px] overflow-auto rounded-md border bg-muted/50 p-2 text-[11px] leading-relaxed whitespace-pre">{d.source}</pre></F>
          </>}
          {selNode.type === 'condition' && <>
            <F label="State field để rẽ nhánh"><Sel value={d.field} onChange={v => upd('field', v)} opts={fieldNames} /></F>
            <F label="Default label (tuỳ chọn)"><Input value={d.default || ''} onChange={e => upd('default', e.target.value)} /></F>
            <p className="text-[11px] text-muted-foreground">Giá trị field được so khớp với label của các edge ra.</p>
          </>}
          {!source && <Button variant="destructive" size="sm" onClick={() => { setNodes(ns => ns.filter(n => n.id !== selNode.id)); setEdges(es => es.filter(e => e.source !== selNode.id && e.target !== selNode.id)); setSel(null) }}><Trash2 />Xoá node</Button>}
        </div>}
      </div></ScrollArea>
    </aside>

    {/* Bottom run panel */}
    <section className="col-span-3 border-t min-h-0 flex flex-col">
      <Tabs value={tab} onValueChange={setTab} className="flex-1 min-h-0 flex flex-col gap-0">
        <div className="flex items-center gap-3 px-3 py-2 border-b">
          <TabsList><TabsTrigger value="input">Input</TabsTrigger><TabsTrigger value="logs">Logs {trace.spans.length > 0 && <Badge variant={trace.status === 'error' ? 'destructive' : 'secondary'} className="ml-1">{trace.spans.length}</Badge>}</TabsTrigger>
            <TabsTrigger value="history">History</TabsTrigger></TabsList>
          {errors.length > 0 && <Badge variant="destructive">{errors.length} lỗi</Badge>}
        </div>
        <TabsContent value="input" className="flex-1 min-h-0 p-3 flex gap-3">
          <Textarea className="font-mono text-xs flex-1 resize-none h-full" value={input} onChange={e => setInput(e.target.value)} />
          {errors.length > 0 && <ScrollArea className="w-1/2"><Alert variant="destructive" id="validation-errors"><AlertTriangle /><AlertTitle>{errors.length} lỗi cần sửa</AlertTitle>
            <AlertDescription><ul className="list-disc pl-4 space-y-0.5 text-xs">{errors.map((e, i) => <li key={i} className="break-words">{e}</li>)}</ul></AlertDescription></Alert></ScrollArea>}
        </TabsContent>
        <TabsContent value="logs" className="flex-1 min-h-0">
          <RunTrace trace={trace} events={log as any} meta={traceMeta} selected={traceSel} onSelect={sp => setTraceSel(sp?.key ?? null)}
            replay={replay ?? undefined} onExitReplay={() => { setReplay(null); setLog([]); setTraceSel(null) }} />
        </TabsContent>
        <TabsContent value="history" className="flex-1 min-h-0">
          <ScrollArea className="h-full"><div className="p-3 space-y-1">
            {!history.length && <span className="text-muted-foreground text-xs">Chưa có lần chạy nào.</span>}
            {history.map(h => <button key={h.id} onClick={() => { setLog(h.events); setReplay(h.id); setTraceSel(null); setTab('logs') }}
              className="w-full flex items-center gap-3 rounded-md px-2 py-1.5 text-left text-xs hover:bg-accent">
              <Badge variant={h.status === 'ok' ? 'success' : h.status === 'timeout' ? 'warning' : h.status === 'cancelled' ? 'secondary' : 'destructive'}>{h.status}</Badge>
              <span className="text-muted-foreground w-20">{new Date(h.started * 1000).toLocaleTimeString()}</span>
              <span className="font-mono text-muted-foreground">{h.id}</span>
              <span className="truncate">{JSON.stringify(h.input)}</span>
              <span className="ml-auto text-muted-foreground">{Math.round((h.ended - h.started) * 1000)} ms</span>
            </button>)}
          </div></ScrollArea>
        </TabsContent>
      </Tabs>
    </section>
  </div>
}
