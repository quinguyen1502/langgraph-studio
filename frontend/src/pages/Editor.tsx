import { Fragment, useCallback, useEffect, useMemo, useRef, useState } from 'react'
import {
  ReactFlow, ReactFlowProvider, Background, Controls, MiniMap, Handle, Position, addEdge,
  useNodesState, useEdgesState, useReactFlow, type Node, type Edge, type Connection, type NodeProps,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import { Keyboard, Redo2, Undo2, Play, Save, Brain, Wrench, GitBranch, Flag, CirclePlay, Plus, Trash2, Braces, Workflow, Loader2, CheckCircle2, XCircle, Code2, Sparkles, GitFork, ExternalLink, UserCheck, Merge, Layers, Database, Plug, type LucideIcon, CopyPlus, Network, ArrowRight, ArrowDown, Check, MoreHorizontal, History, LayoutTemplate, Share2, Webhook, Search, Maximize, Copy, Scissors, ClipboardPaste, BoxSelect, ZoomIn, ZoomOut } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator, DropdownMenuShortcut, DropdownMenuTrigger } from '@/components/ui/dropdown-menu'
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
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog'
import { cn } from '@/lib/utils'
import { useParams, useSearchParams, Link, useNavigate } from 'react-router-dom'
import { HumanPanel } from '@/components/human-panel'
import { ApiTriggerDialog } from '@/components/api-trigger-dialog'
import { VersionsDialog } from '@/components/versions-dialog'
import { ShareDialog } from '@/components/share-dialog'
import { SaveTemplateDialog } from '@/components/save-template-dialog'
import { freeSpot, menuSections, openPalette, registerCommands, type PaletteCommand } from '@/lib/palette'
import { useDeleteWorkflow } from '@/components/delete-workflow'
import { isMac, keyCaps } from '@/lib/shortcuts'
const isMacPlatform = isMac()
import { SHORTCUTS } from '@/lib/shortcuts'
import { layoutGraph, type Direction } from '@/lib/layout'
import { clipStore, copySelection, pasteClip, type Clip } from '@/lib/clipboard'
import { canEdit, type Access } from '@/lib/rbac'
import { ArrowLeft, Square, AlertTriangle } from 'lucide-react'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { api, wsUrl, sessionExpired, tokenValid } from '@/lib/api'
import i18n, { eventErrors } from '@/lib/i18n'
import { useTranslation } from 'react-i18next'
import { LanguageSwitcher } from '@/components/language-switcher'
import { useTheme, ThemeToggle } from '@/lib/theme'
import { UserMenu } from '@/components/user-menu'
import { HumanApprovalSettings } from '@/components/human-approval-settings'
import type { Channels } from '@/lib/approvals'
import { PendingBadge } from '@/components/pending-badge'
import { NotificationBell } from '@/components/notification-bell'
import type { Credential } from '@/components/credentials-dialog'
import { ModelPicker } from '@/components/model-picker'
import { useProviders } from '@/lib/providers'
import { RunTrace } from '@/components/run-trace'
import { buildTrace, fmtCost, fmtMs, withSummary } from '@/lib/trace'
import { SubgraphSettings } from '@/components/subgraph-settings'
import { RetrieverSettings } from '@/components/retriever-settings'
import { McpSettings } from '@/components/mcp-settings'
import { ShortcutCheatsheet } from '@/components/shortcut-cheatsheet'
import { useShortcuts } from '@/lib/use-shortcuts'
import { useGraphHistory } from '@/lib/use-graph-history'
import { PROTECTED, removeElements, selectionIds } from '@/lib/graph-ops'

type Field = { name: string; type: string; reducer?: string }
type LogItem = { type: string; node?: string; label?: string; duration_ms?: number; delta?: any; state?: any; errors?: string[]; error?: any }
/** `desc` is resolved via i18n key `nodes.<type>`. */
const META: Record<string, { label: string; icon: LucideIcon; color: string; accent: string }> = {
  start: { label: 'Start', icon: CirclePlay, color: 'bg-node-start-muted text-node-start', accent: 'bg-node-start' },
  llm: { label: 'LLM', icon: Brain, color: 'bg-node-llm-muted text-node-llm', accent: 'bg-node-llm' },
  tool: { label: 'Tool/API', icon: Wrench, color: 'bg-node-tool-muted text-node-tool', accent: 'bg-node-tool' },
  condition: { label: 'Condition', icon: GitBranch, color: 'bg-node-condition-muted text-node-condition', accent: 'bg-node-condition' },
  end: { label: 'End', icon: Flag, color: 'bg-node-end-muted text-node-end', accent: 'bg-node-end' },
  human: { label: 'Human', icon: UserCheck, color: 'bg-node-human-muted text-node-human', accent: 'bg-node-human' },
}
META.join = { label: 'Join', icon: Merge, color: 'bg-node-join-muted text-node-join', accent: 'bg-node-join' }
META.subgraph = { label: 'Subgraph', icon: Layers, color: 'bg-node-subgraph-muted text-node-subgraph', accent: 'bg-node-subgraph' }
META.subgraph_exit = META.subgraph
META.mcp = { label: 'MCP tool', icon: Plug, color: 'bg-node-mcp-muted text-node-mcp', accent: 'bg-node-mcp' }
META.retriever = { label: 'Retriever', icon: Database, color: 'bg-node-retriever-muted text-node-retriever', accent: 'bg-node-retriever' }
META.code = { label: 'Code', icon: Code2, color: 'bg-node-code-muted text-node-code', accent: 'bg-node-code' }
const TYPES = ['start', 'llm', 'retriever', 'tool', 'mcp', 'condition', 'human', 'join', 'subgraph', 'end']
/** Reducers per field type (TASK-0011): how parallel writes combine. */
const REDUCERS: Record<string, string[]> = { list: ['replace', 'append'], object: ['replace', 'merge'], number: ['replace', 'add'], integer: ['replace', 'add'] }
/** Trace events of nodes inside a subgraph carry `sub/inner` ids: the canvas shows them on the subgraph node. */
const canvasId = (nid: string) => nid.split('/')[0]

const styleEdges = (es: any[]): Edge[] => es.map(e => e.conditional ? { ...e, animated: true, style: { strokeDasharray: '6 4' }, labelBgPadding: [6, 3], labelBgBorderRadius: 4 } : e)
function defaultInput(state: Field[]) {
  return JSON.stringify(Object.fromEntries(state.map(f => [f.name, f.type === 'list' ? [{ role: 'user', content: i18n.t('samples.greeting') }] : f.type === 'number' || f.type === 'integer' ? 0 : f.type === 'boolean' ? false : f.type === 'object' ? {} : 'hello'])), null, 2)
}
const DEFAULTS: Record<string, any> = {
  start: { label: 'Start' }, end: { label: 'End' },
  llm: { label: 'LLM', model: 'gpt-4o-mini', prompt: '', output_field: '' }, // prompt comes from i18n `samples.prompt` on drop
  tool: { label: 'Tool', mode: 'function', function: 'lookup_order', method: 'GET', url: '', body: '', output_field: '' },
  condition: { label: 'Condition', field: '', default: '' },
  human: { label: 'Approval', prompt: '', output_field: '' },
  mcp: { label: 'MCP tool', server_id: '', tool: '', arguments: {}, output_field: '' },
  retriever: { label: 'Retriever', knowledge_base_id: '', query: '{{state.message}}', top_k: 4, output_field: '' },
  join: { label: 'Join' }, subgraph: { label: 'Subgraph', workflow_id: '' }, // response (text, or approved / rejected) goes to output_field
}

function StatusBadge({ s }: { s?: string }) {
  const { t } = useTranslation()
  if (s === 'running') return <Badge variant="warning" className="gap-1"><Loader2 className="size-3 animate-spin" />{t('status.running')}</Badge>
  if (s === 'done') return <Badge variant="success" className="gap-1"><CheckCircle2 className="size-3" />{t('status.done')}</Badge>
  if (s === 'error') return <Badge variant="destructive" className="gap-1"><XCircle className="size-3" />{t('status.error')}</Badge>
  if (s === 'waiting') return <Badge variant="outline" className="gap-1 border-node-human text-node-human"><UserCheck className="size-3" />{t('status.waiting')}</Badge>
  if (s === 'cancelled') return <Badge variant="secondary" className="gap-1"><Square className="size-3" />{t('status.cancelled')}</Badge>
  return null
}

function StudioNode({ data, type, selected }: NodeProps) {
  const d = data as any; const m = META[type!]; const I = m.icon
  return <div className={cn(type === 'code' && 'border-node-code/60 border-dashed', 'relative rounded-xl border bg-card text-card-foreground shadow-sm px-3 py-2 min-w-44 transition-all',
    selected && 'ring-2 ring-ring', d._hl && 'ring-4 ring-primary/40 shadow-md', d._status === 'running' && 'border-warning ring-4 ring-warning/30',
    d._status === 'done' && 'border-success', d._status === 'waiting' && 'border-node-human ring-4 ring-node-human/30', d._status === 'error' && 'border-destructive')}>
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
/** Where registry actions appear in the editor's ⋯ menu (others stay keyboard/palette only), with stable ids for tests. */
const MENU_OF: Record<string, 'arrange' | 'help' | undefined> = { layout: 'arrange', fitView: 'arrange', cheatsheet: 'help' }
const MENU_IDS: Record<string, string> = { layout: 'layout-btn', fitView: 'fit-btn', cheatsheet: 'shortcuts-btn' }
const ACTION_ICONS: Record<string, LucideIcon> = { layout: Network, fitView: Maximize, cheatsheet: Keyboard, save: Save, run: Play, stop: Square, undo: Undo2, redo: Redo2, delete: Trash2, copy: Copy, cut: Scissors, paste: ClipboardPaste, duplicate: CopyPlus, selectAll: BoxSelect, zoomIn: ZoomIn, zoomOut: ZoomOut }
const nodeTypes = Object.fromEntries([...TYPES, 'code'].map(t => [t, StudioNode]))

function Tip({ tip, children }: { tip: string; children: React.ReactElement }) {
  return <Tooltip><TooltipTrigger asChild>{children}</TooltipTrigger><TooltipContent>{tip}</TooltipContent></Tooltip>
}

function Sel({ value, onChange, opts, ph }: { value?: string; onChange: (v: string) => void; opts: string[]; ph?: string }) {
  const { t } = useTranslation()
  return <Select value={value || undefined} onValueChange={onChange}>
      <SelectTrigger className="w-full"><SelectValue placeholder={ph || t('common.choose')} /></SelectTrigger>
      <SelectContent>{opts.filter(Boolean).map(o => <SelectItem key={o} value={o}>{o}</SelectItem>)}</SelectContent>
    </Select>
}
const F = ({ label, children }: { label: string; children: React.ReactNode }) => <div className="space-y-1.5"><Label className="text-xs text-muted-foreground">{label}</Label>{children}</div>

export function EditorPage() { return <ReactFlowProvider><Studio /></ReactFlowProvider> }

function Studio() {
  const { t } = useTranslation(); const { id } = useParams(); const [params] = useSearchParams()
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([])
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([])
  const [state, setState] = useState<Field[]>([])
  const [name, setName] = useState('Untitled')
  const [wid, setWid] = useState<string | undefined>()
  const [sel, setSel] = useState<{ kind: 'node' | 'edge'; id: string } | null>(null)
  const [input, setInput] = useState(() => i18n.t('samples.input'))
  const [log, setLog] = useState<LogItem[]>([])
  const [errors, setErrors] = useState<string[]>([])
  const [tools, setTools] = useState<{ name: string }[]>([])
  const [mode, setMode] = useState('')
  const [source, setSource] = useState<any>(null)
  const [creds, setCreds] = useState<Credential[]>([])
  const providers = useProviders()
  const [channels, setChannels] = useState<Channels | null>(null)
  const [history, setHistory] = useState<any[]>([])
  const [tab, setTab] = useState('input')
  const [running, setRunning] = useState(false)
  const [traceSel, setTraceSel] = useState<string | null>(null); const [replay, setReplay] = useState<string | null>(null)
  const [loadErr, setLoadErr] = useState<{ status: number; msg: string } | null>(null)
  const [access, setAccess] = useState<Access>('owner'); const [ownerEmail, setOwnerEmail] = useState<string | null>(null)
  const edit = canEdit(access)  // viewers (share or global role) get a read-only editor; they can still run (TASK-0014)
  const { dark } = useTheme()
  const rf = useReactFlow(); const idc = useRef(1); const wsRef = useRef<WebSocket | null>(null)

  // unsaved-changes tracking (TASK-0019): snapshot of the saved graph, taken after load/save
  const savedSnap = useRef<string | null>(null); const takeBaseline = useRef(false)
  const snap = () => { const { id: _id, ...rest } = toJSON(); return JSON.stringify(rest) }
  // undo/redo (TASK-0024): snapshots of nodes, edges and the state schema; reset whenever a workflow is (re)loaded
  const hist = useGraphHistory(nodes, edges, state, h => { setNodes(h.nodes.map(n => ({ ...n }))); setEdges(styleEdges(h.edges)); setState(h.state) })
  useEffect(() => { if (takeBaseline.current) { takeBaseline.current = false; savedSnap.current = snap(); hist.reset(nodes, edges, state) } }, [nodes, edges, name, state])
  const load = (wf: any) => {
    takeBaseline.current = true
    setName(wf.name); setWid(wf.id); setState(wf.state || [])
    setSource(wf.source || null)
    if (wf.access) { setAccess(wf.access); setOwnerEmail(wf.mine ? null : wf.owner_email ?? null) }
    setNodes(wf.needs_layout ? layoutGraph(wf.nodes, wf.edges, 'LR', false) : wf.nodes); setEdges(styleEdges(wf.edges))
    if (wf.source) setInput(defaultInput(wf.state || []))
  }
  const loadHistory = (id?: string) => id ? api<any[]>(`/api/workflows/${id}/runs`).then(hs => { setHistory(hs); return hs }) : undefined
  const openRun = (h: any) => { setLog(withSummary(h)); setReplay(h.id); setTraceSel(null); setTab('logs') }
  useEffect(() => {
    api(`/api/workflows/${id}`).then(wf => { setLoadErr(null); load(wf)
      // ?run=<id> (from the pending list) opens that run with its Human panel
      loadHistory(wf.id)?.then((hs: any[]) => { const h = hs?.find(x => x.id === params.get('run')); if (h) openRun(h) }) })
      .catch(e => setLoadErr({ status: e.status ?? 0, msg: e.message }))
    api('/api/tools').then(setTools).catch(() => {})
    api<Credential[]>('/api/credentials').then(setCreds).catch(() => {})
    api<Channels>('/api/approvals/channels').then(setChannels).catch(() => {})
    api('/api/health').then(h => setMode(h.llm_mode)).catch(() => {})
  }, [id])

  const toJSON = () => ({
    id: wid, name, state,
    nodes: nodes.map(n => ({ id: n.id, type: n.type, position: n.position, data: Object.fromEntries(Object.entries(n.data).filter(([k]) => !k.startsWith('_'))) })),
    edges: edges.map(e => ({ id: e.id, source: e.source, target: e.target, ...(e.label ? { label: String(e.label) } : {}), ...((e as any).conditional ? { conditional: true } : {}) })),
  })
  const save = async () => {
    try {
      const r = await api('/api/workflows', { method: 'POST', json: toJSON() })
      setWid(r.id); setErrors(r.errors); savedSnap.current = snap(); if (r.errors.length) setTab('input')
    } catch (e: any) { setErrors([t('editor.saveFailed', { error: e.message })]); setTab('input') }
  }
  const mark = (id: string, patch: any) => setNodes(ns => ns.map(n => n.id === id ? { ...n, data: { ...n.data, ...patch } } : n))
  /** One socket path for new runs and for resuming a waiting run (the resumed events append to the same log). */
  const stream = (msg: any, resume = false) => {
    if (!tokenValid()) { setErrors([t('editor.expiredRedirect')]); setTab('logs'); setTimeout(sessionExpired, 1500); return }
    setErrors([]); setTab('logs'); setRunning(true); setTraceSel(null)
    if (resume) setLog(l => l.filter(e => e.type !== 'run_summary'))
    else { setLog([]); setReplay(null); setNodes(ns => ns.map(n => ({ ...n, data: { ...n.data, _status: '', _dur: null } }))) }
    const ws = new WebSocket(wsUrl('/ws/run')); wsRef.current = ws
    ws.onopen = () => ws.send(JSON.stringify(msg))
    ws.onmessage = m => {
      const ev: LogItem = JSON.parse(m.data); setLog(l => [...l, ev])
      if (ev.type === 'node_started') mark(canvasId(ev.node!), { _status: 'running' })
      if (ev.type === 'run_waiting') mark(canvasId(ev.node!), { _status: 'waiting' })
      if (ev.type === 'node_finished') mark(canvasId(ev.node!), ev.node!.includes('/') ? { _status: 'done' } : { _status: 'done', _dur: ev.duration_ms })
      if (ev.type === 'error') { setErrors(eventErrors(ev)); if (ev.node) mark(canvasId(ev.node), { _status: 'error' }) }
      if (ev.type === 'run_cancelled' || (ev.type === 'error' && (ev as any).status === 'timeout')) setNodes(ns => ns.map(n => n.data._status === 'running' ? { ...n, data: { ...n.data, _status: 'cancelled' } } : n))
    }
    ws.onerror = () => setErrors(e => e.length ? e : [t('editor.wsLost')])
    ws.onclose = ev => {
      if (ev.code === 4401) { setErrors([t('editor.expiredDuringRun')]); setTimeout(sessionExpired, 1500) }
      setRunning(false); setNodes(ns => ns.map(n => n.data._status === 'running' ? { ...n, data: { ...n.data, _status: 'error' } } : n)); loadHistory(wid) }
  }
  const run = () => {
    let inp: any; try { inp = JSON.parse(input) } catch { setErrors([t('editor.badInput')]); setTab('input'); return }
    stream({ workflow_id: wid, workflow: toJSON(), input: inp })
  }
  const respond = (runId: string, response: string) => stream({ resume_run_id: runId, response }, true)
  const cancelRun = () => wsRef.current?.readyState === WebSocket.OPEN && wsRef.current.send(JSON.stringify({ type: 'cancel' }))
  const removeIds = (nodeIds: string[], edgeIds: string[] = []) => {
    const r = removeElements(nodes, edges, nodeIds, edgeIds); if (!r.removed) return
    setNodes(r.nodes); setEdges(r.edges); if (sel && (nodeIds.includes(sel.id) || edgeIds.includes(sel.id))) setSel(null)
  }
  // clipboard (TASK-0026, DEC-0029): pure copy/paste in lib/clipboard.ts; one paste = one render = one undo step
  const clipMem = useRef<Clip | null>(null); const pasteN = useRef(0)
  const [clipNote, setClipNote] = useState(''); const noteTimer = useRef<number>(0)
  const note = (m: string) => { setClipNote(m); window.clearTimeout(noteTimer.current); noteTimer.current = window.setTimeout(() => setClipNote(''), 2500) }
  const selClip = () => { const s = selectionIds(nodes, edges, sel); return copySelection(nodes, edges, s.nodeIds) }
  const insert = (clip: Clip, n: number) => {
    const sameCanvas = clip.nodes.some(c => nodes.some(x => x.id === c.id))
    const view = rf.screenToFlowPosition({ x: window.innerWidth / 2 - 120, y: window.innerHeight / 2 - 60 })
    const r = pasteClip(clip, { existing: nodes.map(x => x.id), usableCredentials: new Set(creds.map(c => c.id)), offset: 40 * n, at: sameCanvas ? undefined : view })
    setNodes(ns => [...ns.map(x => x.selected ? { ...x, selected: false } : x), ...r.nodes]); setEdges(es => [...es.map(x => x.selected ? { ...x, selected: false } : x), ...styleEdges(r.edges)])
    setSel(r.nodes.length === 1 ? { kind: 'node', id: r.nodes[0].id } : null)
    note(r.clearedCredentials ? t('clipboard.pastedCleared', { count: r.nodes.length, creds: r.clearedCredentials }) : t('clipboard.pasted', { count: r.nodes.length }))
  }
  const copy = (cut = false) => {
    const c = selClip(); if (!c) return false
    clipMem.current = c; pasteN.current = 0; clipStore.write(c)
    if (cut) { removeIds(c.nodes.map(n => n.id)); note(t('clipboard.cut', { count: c.nodes.length })) } else note(t('clipboard.copied', { count: c.nodes.length }))
  }
  const editable = edit && !source
  // auto-layout (TASK-0027, DEC-0030): one setNodes = one undo step; direction remembered per browser
  const [layoutDir, setLayoutDir] = useState<Direction>(() => (localStorage.getItem('lgs.layoutDir') as Direction) === 'TB' ? 'TB' : 'LR')
  const tidy = (dir: Direction = layoutDir) => {
    if (!editable) return false
    if (dir !== layoutDir) { setLayoutDir(dir); localStorage.setItem('lgs.layoutDir', dir) }
    setNodes(ns => layoutGraph(ns, edges, dir)); window.setTimeout(() => rf.fitView({ duration: 250 }), 30)
  }
    // keyboard shortcuts (TASK-0023): one registry (lib/shortcuts.ts) drives this map and the cheat sheet
  const [cheat, setCheat] = useState(false)
  const handlers: Record<string, () => void | boolean> = {
    save: () => { if (edit) save() },
    run: () => { if (!running) run() },
    stop: () => { if (running) cancelRun() },
    delete: () => { if (!edit || source) return false; const s = selectionIds(nodes, edges, sel); removeIds(s.nodeIds, s.edgeIds) },
    selectAll: () => { setNodes(ns => ns.map(n => ({ ...n, selected: true }))); setEdges(es => es.map(e => ({ ...e, selected: true }))) },
    fitView: () => { rf.fitView({ duration: 200 }) },
    zoomIn: () => { rf.zoomIn({ duration: 150 }) },
    zoomOut: () => { rf.zoomOut({ duration: 150 }) },
    escape: () => { setSel(null); setNodes(ns => ns.map(n => n.selected ? { ...n, selected: false } : n)); setEdges(es => es.map(e => e.selected ? { ...e, selected: false } : e)); return false },
    cheatsheet: () => setCheat(true),
    layout: () => tidy(),
    copy: () => copy(),
    cut: () => editable ? copy(true) : false,
    paste: () => { if (!editable) return false; const c = clipStore.read() ?? clipMem.current; if (!c) return false; insert(c, ++pasteN.current) },
    duplicate: () => { if (!editable) return false; const c = selClip(); if (!c) return; insert(c, 1) },
    undo: () => { if (edit) hist.undo() },
    redo: () => { if (edit) hist.redo() },
  }
  useShortcuts(handlers)
  // command palette (TASK-0028, DEC-0031): registry actions, add node, jump to node — re-registered each render so closures stay fresh
  const addNode = (type: string, pos: { x: number; y: number }, select = false) => {
    const id = `${type}_${Date.now().toString(36)}${idc.current++}`
    setNodes(ns => [...(select ? ns.map(n => n.selected ? { ...n, selected: false } : n) : ns), { id, type, position: pos, selected: select,
      data: { ...DEFAULTS[type], ...(type === 'llm' ? { prompt: i18n.t('samples.prompt', { var: '{{state.message}}' }) } : {}) } }])
    if (select) setSel({ kind: 'node', id })
  }
  const off: Record<string, boolean> = { save: !edit, run: running, stop: !running, undo: !hist.canUndo, redo: !hist.canRedo,
    ...Object.fromEntries(['delete', 'cut', 'paste', 'duplicate', 'layout'].map(k => [k, !editable])) }
  const paletteRef = useRef<Record<string, () => void>>({})
  // secondary editor actions (TASK-0028 follow-up): one list feeds the ⋯ menu and the command palette
  const [dlg, setDlg] = useState<null | 'share' | 'versions' | 'api' | 'template' | 'json'>(null)
  const nav = useNavigate(); const delWf = useDeleteWorkflow(() => nav('/workflows'))
  const isDirty = () => savedSnap.current !== null && snap() !== savedSnap.current
  const menuExtras: PaletteCommand[] = [
    ...(['LR', 'TB'] as Direction[]).map(d => ({ id: `action:layout${d}`, group: 'actions' as const, label: `${t('layout.button')}: ${t(d === 'LR' ? 'layout.lr' : 'layout.tb')}`, icon: d === 'LR' ? ArrowRight : ArrowDown,
      menu: 'arrange' as const, elementId: `layout-${d.toLowerCase()}`, disabled: !editable, hint: layoutDir === d ? '✓' : undefined, run: () => { tidy(d) } })),
    { id: 'action:versions', group: 'actions', label: t('versions.button'), icon: History, menu: 'workflow', elementId: 'versions-btn', disabled: !wid, run: () => setDlg('versions') },
    { id: 'action:saveTemplate', group: 'actions', label: t('templates.saveAs'), icon: LayoutTemplate, menu: 'workflow', elementId: 'save-template-btn', disabled: !edit || !wid, run: () => setDlg('template') },
    { id: 'action:share', group: 'actions', label: t('share.button'), icon: Share2, menu: 'workflow', elementId: 'share-btn', disabled: !wid, run: () => setDlg('share') },
    { id: 'action:api', group: 'actions', label: t('api.button'), icon: Webhook, menu: 'workflow', elementId: 'api-btn', disabled: !wid || access !== 'owner', run: () => setDlg('api') },
    { id: 'action:json', group: 'actions', label: t('editor.jsonTitle'), icon: Braces, menu: 'workflow', elementId: 'json-btn', run: () => setDlg('json') },
    { id: 'action:openPalette', group: 'actions', label: t('palette.title'), icon: Search, shortcut: 'palette', menu: 'help', elementId: 'palette-btn', run: openPalette },
    { id: 'action:deleteWorkflow', group: 'actions', label: t('editor.deleteWorkflow'), icon: Trash2, menu: 'danger', destructive: true, elementId: 'delete-wf-btn',
      disabled: !wid || access !== 'owner', run: () => { if (wid) delWf.ask({ id: wid, name }) } },
  ]
  const paletteCmds: PaletteCommand[] = [
    ...SHORTCUTS.filter(x => handlers[x.id] && x.id !== 'escape').map(x => ({ id: `action:${x.id}`, group: 'actions' as const, label: t(`shortcuts.actions.${x.id}`), shortcut: x.id, disabled: off[x.id],
      icon: ACTION_ICONS[x.id], menu: MENU_OF[x.id], elementId: MENU_IDS[x.id], run: () => { handlers[x.id]() } })),
    ...menuExtras,
    ...(editable ? TYPES.filter(x => x !== 'start' && x !== 'end').map(x => ({ id: `add:${x}`, group: 'add' as const, label: t('palette.addNode', { type: META[x].label }), hint: t(`nodes.${x}`), icon: META[x].icon, keywords: [x],
      run: () => { const c = rf.screenToFlowPosition({ x: window.innerWidth / 2, y: window.innerHeight / 2 }); addNode(x, freeSpot(c, nodes.map(n => n.position)), true) } })) : []),
    ...nodes.map(n => ({ id: `node:${n.id}`, group: 'nodes' as const, label: String((n.data as any)?.label || n.id), hint: `${META[n.type!]?.label ?? n.type} · ${n.id}`, icon: META[n.type!]?.icon, keywords: [n.id, n.type!],
      run: () => { setNodes(ns => ns.map(x => ({ ...x, selected: x.id === n.id }))); setSel({ kind: 'node', id: n.id }); rf.fitView({ nodes: [{ id: n.id }], duration: 300, maxZoom: 1.2 }) } })),
  ]
  paletteCmds.forEach(c => { paletteRef.current[c.id] = c.run })
  const paletteSig = paletteCmds.map(c => `${c.id}|${c.label}|${c.hint ?? ''}|${c.disabled ? 1 : 0}`).join('\n')
  // re-register only when the visible content changes (runs read the latest closures through paletteRef)
  // oxlint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => registerCommands('editor', paletteCmds.map(c => ({ ...c, run: () => paletteRef.current[c.id]?.() }))), [paletteSig])

  const trace = useMemo(() => buildTrace(log as any, nid => { const n = nodes.find(x => x.id === nid); return { label: (n?.data as any)?.label, type: n?.type } }), [log, nodes])
  const traceMeta = (t: string) => META[t] || META.code
  const hlSpan = traceSel ? trace.spans.find(x => x.key === traceSel)?.node : undefined
  const hlNode = hlSpan ? canvasId(hlSpan) : undefined
  const nodesView = useMemo(() => hlNode ? nodes.map(n => n.id === hlNode ? { ...n, data: { ...n.data, _hl: true } } : n) : nodes, [nodes, hlNode])
  const onNodeClick = (id: string) => {
    setSel({ kind: 'node', id })
    const spans = trace.spans.filter(x => canvasId(x.node) === id)
    if (spans.length) {
      const cur = spans.findIndex(x => x.key === traceSel) // repeated clicks cycle through loop iterations
      setTraceSel(spans[cur >= 0 ? (cur + 1) % spans.length : spans.length - 1].key); setTab('logs')
    }
  }
  const onConnect = useCallback((c: Connection) => setEdges(es => addEdge({ ...c, id: 'e' + Date.now() }, es)), [])
  const onDrop = (ev: React.DragEvent) => {
    ev.preventDefault(); if (!edit) return; const t = ev.dataTransfer.getData('nodetype'); if (!t) return
    addNode(t, rf.screenToFlowPosition({ x: ev.clientX, y: ev.clientY }))
  }
  const selNode = sel?.kind === 'node' ? nodes.find(n => n.id === sel.id) : undefined
  const selEdge = sel?.kind === 'edge' ? edges.find(e => e.id === sel.id) : undefined
  const upd = (k: string, v: any) => selNode && mark(selNode.id, { [k]: v })
  const d: any = selNode?.data || {}
  const fieldNames = state.map(f => f.name)

  if (loadErr) return <div className="min-h-screen flex items-center justify-center bg-muted/40 p-4 text-foreground">
    <div className="max-w-sm text-center space-y-3 rounded-xl border bg-card p-8 shadow-sm" id="editor-not-found">
      <div className="mx-auto w-fit rounded-full bg-muted p-3 text-muted-foreground"><ArrowLeft className="size-5" /></div>
      <h1 className="text-lg font-semibold">{t(loadErr.status === 404 ? 'editor.notFoundTitle' : 'editor.openFailedTitle')}</h1>
      <p className="text-sm text-muted-foreground">{loadErr.status === 404 ? t('editor.notFoundBody') : loadErr.msg}</p>
      <Button asChild><Link to="/workflows" id="back-to-list">{t('editor.backToList')}</Link></Button>
    </div>
  </div>

  return <div className="h-screen grid grid-rows-[56px_1fr_300px] grid-cols-[250px_1fr_320px] bg-background text-foreground text-sm">
    {/* Top bar */}
    <header className="col-span-3 flex items-center gap-3 border-b px-4">
      <Tip tip={t('editor.backToList')}><Button variant="ghost" size="icon" asChild><Link to="/workflows" id="back-btn"><ArrowLeft /></Link></Button></Tip>
      <div className="flex items-center gap-2 font-semibold"><div className="rounded-md bg-primary text-primary-foreground p-1.5"><Workflow className="size-4" /></div>LangGraph Studio</div>
      <Separator orientation="vertical" className="h-6!" />
      <Input value={name} readOnly={!edit} onChange={e => setName(e.target.value)} className="w-72 min-w-44 h-8" aria-label={t('editor.nameLabel')} />
      {edit && savedSnap.current !== null && snap() !== savedSnap.current && <Badge variant="outline" id="unsaved-badge" className="border-warning text-warning">{t('history.unsaved')}</Badge>}
      {!edit && <Badge variant="secondary" id="view-only" title={ownerEmail ?? ''}>{t('editor.viewOnly')}</Badge>}
      {edit && ownerEmail && <Badge variant="outline" id="shared-editor" title={ownerEmail}>{t('list.sharedBy', { email: ownerEmail })}</Badge>}
      <Tip tip={t('editor.saveTip')}><Button variant="outline" size="sm" id="save-btn" onClick={save} disabled={!edit}><Save />{t('common.save')}</Button></Tip>
      <Tip tip={t('editor.runTip')}><Button size="sm" id="run-btn" onClick={run} disabled={running}>{running ? <Loader2 className="animate-spin" /> : <Play />}{t('editor.run')}</Button></Tip>
      {running && <Tip tip={t('editor.cancelTip')}><Button size="sm" variant="outline" id="cancel-btn" onClick={cancelRun}><Square />{t('common.cancel')}</Button></Tip>}
      {edit && <div className="flex items-center" role="group" aria-label={t('history.group')}>
        <Tip tip={t('history.undoTip')}><Button variant="ghost" size="icon" id="undo-btn" aria-label={t('history.undo')} disabled={!hist.canUndo} onClick={hist.undo}><Undo2 /></Button></Tip>
        <Tip tip={t('history.redoTip')}><Button variant="ghost" size="icon" id="redo-btn" aria-label={t('history.redo')} disabled={!hist.canRedo} onClick={hist.redo}><Redo2 /></Button></Tip></div>}
      <DropdownMenu>
        <Tip tip={t('editor.moreTip')}><DropdownMenuTrigger asChild><Button variant="ghost" size="icon" id="more-btn" aria-label={t('editor.more')}><MoreHorizontal /></Button></DropdownMenuTrigger></Tip>
        <DropdownMenuContent align="start" className="min-w-64" id="more-menu">
          {menuSections(paletteCmds).map(([sec, items], k) => <Fragment key={sec}>{k > 0 && <DropdownMenuSeparator />}
            {items.map(c => { const I = c.icon; const combo = c.shortcut ? SHORTCUTS.find(x => x.id === c.shortcut)?.keys[0] : undefined
              return <DropdownMenuItem key={c.id} id={c.elementId} data-testid="more-item" disabled={c.disabled} variant={c.destructive ? 'destructive' : 'default'} onSelect={() => c.run()}>
                {I && <I className={c.id === 'action:layout' && layoutDir === 'TB' ? 'rotate-90' : undefined} />}<span>{c.label}</span>
                {c.hint === '✓' && <Check className="ml-auto" />}
                {combo && <DropdownMenuShortcut>{keyCaps(combo).join(isMacPlatform ? '' : '+')}</DropdownMenuShortcut>}
              </DropdownMenuItem> })}</Fragment>)}
        </DropdownMenuContent>
      </DropdownMenu>
      <ShortcutCheatsheet open={cheat} onOpenChange={setCheat} />
      {wid && <ShareDialog workflowId={wid} open={dlg === 'share'} onOpenChange={v => setDlg(v ? 'share' : null)} onTransferred={(o, f) => { setErrors(f.length ? [t('transfer.done', { email: o }), ...f.map(i => t('transfer.flaggedLine', { node: i.node, kind: t(`transfer.kinds.${i.kind}`), name: i.name ?? i.id }))] : [t('transfer.done', { email: o })]); setTab('input'); api(`/api/workflows/${wid}`).then(load).catch(() => {}) }} />}
      {edit && <SaveTemplateDialog wid={wid} defaultName={name} isDirty={isDirty} open={dlg === 'template'} onOpenChange={v => setDlg(v ? 'template' : null)} />}
      <VersionsDialog wid={wid} isDirty={isDirty} open={dlg === 'versions'} onOpenChange={v => setDlg(v ? 'versions' : null)} onRestored={wf => { load(wf); setErrors([]) }} />
      {access === 'owner' && <ApiTriggerDialog wid={wid} open={dlg === 'api'} onOpenChange={v => setDlg(v ? 'api' : null)} />}
      <Dialog open={dlg === 'json'} onOpenChange={v => setDlg(v ? 'json' : null)}>
        <DialogContent className="sm:max-w-2xl"><DialogHeader><DialogTitle>{t('editor.jsonTitle')}</DialogTitle><DialogDescription>{t('editor.jsonDesc')}</DialogDescription></DialogHeader>
          <ScrollArea className="h-96 rounded-md border bg-muted/40"><pre className="p-3 text-xs">{JSON.stringify(toJSON(), null, 2)}</pre></ScrollArea>
        </DialogContent>
      </Dialog>
      {delWf.dialog}
      <div className="ml-auto flex items-center gap-2">
        {source && <Tip tip={t('editor.importedTip', { src: source.repo_url || 'zip', ref: source.ref })}><Badge variant="secondary" className="gap-1"><GitFork className="size-3" />{t('editor.imported')}</Badge></Tip>}
        <Badge variant="secondary">{t('editor.llmMode', { mode })}</Badge>{wid && <Badge variant="outline">{t('editor.idBadge', { id: wid })}</Badge>}
        <PendingBadge /><NotificationBell /><LanguageSwitcher /><ThemeToggle /><UserMenu />
      </div>
    </header>

    {/* Left */}
    <aside className="border-r bg-muted/30 min-h-0">
      <ScrollArea className="h-full"><div className="p-3 space-y-4">
        <div>
          <div className="text-xs font-semibold uppercase text-muted-foreground mb-2">{t('editor.palette')}</div>
          <div className="space-y-2">{TYPES.map(t_ => { const m = META[t_]; const I = m.icon
            return <Card key={t_} draggable={edit} onDragStart={e => { e.dataTransfer.setData('nodetype', t_); e.dataTransfer.effectAllowed = 'move' }}
              className="flex-row items-center gap-3 p-2.5 cursor-grab hover:bg-accent transition-colors py-2.5">
              <div className={cn('rounded-md p-1.5', m.color)}><I className="size-4" /></div>
              <div><div className="font-medium leading-tight">{m.label}</div><div className="text-[11px] text-muted-foreground">{t(`nodes.${t_}`)}</div></div>
            </Card> })}</div>
        </div>
        <Separator />
        <div>
          <div className="text-xs font-semibold uppercase text-muted-foreground mb-2">{t('editor.stateSchema')}</div>
          <div className="space-y-1.5">{state.map((f, i) => <div className="space-y-1" key={i}><div className="flex gap-1">
            <Input className="h-8 flex-1 min-w-0" value={f.name} onChange={e => setState(s => s.map((x, j) => j === i ? { ...x, name: e.target.value } : x))} />
            <Select value={f.type} onValueChange={v => setState(s => s.map((x, j) => j === i ? { ...x, type: v, reducer: REDUCERS[v]?.includes(x.reducer || '') ? x.reducer : undefined } : x))}>
              <SelectTrigger size="sm" className="w-24"><SelectValue /></SelectTrigger>
              <SelectContent>{['string', 'number', 'integer', 'boolean', 'object', 'list'].map(t => <SelectItem key={t} value={t}>{t}</SelectItem>)}</SelectContent>
            </Select>
            <Button variant="ghost" size="icon" className="size-8" onClick={() => setState(s => s.filter((_, j) => j !== i))}><Trash2 /></Button>
            </div>
            {REDUCERS[f.type] && <Select value={f.reducer || 'replace'} onValueChange={v => setState(s => s.map((x, j) => j === i ? { ...x, reducer: v === 'replace' ? undefined : v } : x))}>
              <SelectTrigger size="sm" className="w-full text-xs" id={`reducer-${f.name}`} aria-label={t('editor.reducer')}><SelectValue /></SelectTrigger>
              <SelectContent>{REDUCERS[f.type].map(r => <SelectItem key={r} value={r}>{t(`editor.reducers.${r}`)}</SelectItem>)}</SelectContent>
            </Select>}
          </div>)}</div>
          <Button variant="outline" size="sm" className="mt-2 w-full" onClick={() => setState(s => [...s, { name: 'field' + (s.length + 1), type: 'string' }])}><Plus />{t('editor.addField')}</Button>
        </div>
      </div></ScrollArea>
    </aside>

    {/* Canvas */}
    <main className="min-h-0" onDrop={onDrop} onDragOver={e => { e.preventDefault(); e.dataTransfer.dropEffect = 'move' }}>
      {clipNote && <div role="status" id="clip-notice" className="fixed bottom-4 left-1/2 -translate-x-1/2 z-50 rounded-md border bg-popover text-popover-foreground shadow-md px-3 py-1.5 text-sm">{clipNote}</div>}
      <ReactFlow nodes={nodesView} edges={edges} nodeTypes={nodeTypes} onNodesChange={onNodesChange} onEdgesChange={onEdgesChange}
        colorMode={dark ? 'dark' : 'light'} onConnect={edit ? onConnect : undefined} nodesConnectable={edit} nodesDraggable={edit} edgesReconnectable={edit} onNodeClick={(_, n) => onNodeClick(n.id)}
        onEdgeClick={(_, e) => setSel({ kind: 'edge', id: e.id })} onPaneClick={() => setSel(null)} deleteKeyCode={null} fitView>
        <Background /><Controls /><MiniMap pannable zoomable className="[&>svg]:h-20 [&>svg]:w-28" />
      </ReactFlow>
    </main>

    {/* Right config */}
    <aside className="border-l bg-muted/30 min-h-0">
      <ScrollArea className="h-full"><fieldset disabled={!edit} className="contents"><div className="p-4 space-y-4 w-[318px]">
        <div className="text-xs font-semibold uppercase text-muted-foreground">{t('editor.config')}</div>
        {!selNode && !selEdge && <p className="text-muted-foreground text-xs">{t('editor.selectHint')}</p>}
        {selEdge && <div className="space-y-3">
          <Badge variant="outline">Edge {selEdge.source} → {selEdge.target}</Badge>
          <F label={t('editor.edgeLabel')}><Input value={String(selEdge.label || '')} onChange={e => setEdges(es => es.map(x => x.id === selEdge.id ? { ...x, label: e.target.value } : x))} /></F>
          <Button variant="destructive" size="sm" id="delete-edge" onClick={() => removeIds([], [selEdge.id])}><Trash2 />{t('editor.deleteEdge')}</Button>
        </div>}
        {selNode && <div className="space-y-3">
          <div className="flex items-center gap-2">{(() => { const m = META[selNode.type!]; const I = m.icon; return <div className={cn('rounded-md p-1.5', m.color)}><I className="size-4" /></div> })()}
            <div><div className="font-medium">{META[selNode.type!].label}</div><div className="text-[11px] text-muted-foreground font-mono">{selNode.id}</div></div></div>
          <F label={t('field.label')}><Input value={d.label || ''} onChange={e => upd('label', e.target.value)} /></F>
          {selNode.type === 'llm' && <>
            <F label={t('editor.credential')}><Select value={d.credential_id || 'none'} onValueChange={v => upd('credential_id', v === 'none' ? '' : v)}>
              <SelectTrigger className="w-full" id="llm-credential"><SelectValue /></SelectTrigger>
              <SelectContent><SelectItem value="none">{t('editor.credentialDefault')}</SelectItem>
                {creds.map(c => <SelectItem key={c.id} value={c.id}>{c.name} · {c.provider} {c.hint}</SelectItem>)}</SelectContent></Select></F>
            <F label={t('field.model')}><ModelPicker credentialId={d.credential_id || undefined} value={d.model || ''} onChange={v => upd('model', v)} placeholder={providers.find(p => p.id === creds.find(c => c.id === d.credential_id)?.provider)?.default_model || 'gpt-4o-mini'} /></F>
            <F label={t('field.promptTemplate', { field: '{{state.field}}' })}><Textarea rows={7} className="font-mono text-xs" value={d.prompt} onChange={e => upd('prompt', e.target.value)} /></F>
            <F label={t('field.outputField')}><Sel value={d.output_field} onChange={v => upd('output_field', v)} opts={fieldNames} /></F>
          </>}
          {selNode.type === 'human' && <>
            <F label={t('field.humanPrompt', { field: '{{state.field}}' })}><Textarea rows={4} id="human-prompt" className="font-mono text-xs" value={d.prompt} onChange={e => upd('prompt', e.target.value)} /></F>
            <F label={t('field.outputField')}><Sel value={d.output_field} onChange={v => upd('output_field', v)} opts={fieldNames} /></F>
            <HumanApprovalSettings key={selNode.id} value={d.approval} channels={channels} onChange={v => upd('approval', v)} />
          </>}
          {selNode.type === 'tool' && <>
            <F label={t('field.mode')}><Select value={d.mode} onValueChange={v => upd('mode', v)}><SelectTrigger className="w-full"><SelectValue /></SelectTrigger>
              <SelectContent><SelectItem value="function">{t('editor.pyFunction')}</SelectItem><SelectItem value="http">{t('editor.httpRequest')}</SelectItem></SelectContent></Select></F>
            {d.mode === 'http' ? <>
              <F label={t('field.method')}><Sel value={d.method} onChange={v => upd('method', v)} opts={['GET', 'POST', 'PUT', 'DELETE']} /></F>
              <F label={t('field.url')}><Input value={d.url} onChange={e => upd('url', e.target.value)} placeholder="https://…" /></F>
              <F label={t('field.bodyTemplate')}><Textarea rows={4} className="font-mono text-xs" value={d.body} onChange={e => upd('body', e.target.value)} /></F>
            </> : <F label={t('field.function')}><Sel value={d.function} onChange={v => upd('function', v)} opts={tools.map(t => t.name)} /></F>}
            <F label={t('field.outputField')}><Sel value={d.output_field} onChange={v => upd('output_field', v)} opts={fieldNames} /></F>
          </>}
          {selNode.type === 'code' && <>
            <div className="flex flex-wrap gap-1 max-w-[286px]">{d.is_llm && <Badge variant="outline" className="gap-1"><Sparkles className="size-3" />{t('editor.looksLlm')}</Badge>}{d.kind && <Badge variant="secondary">{d.kind}</Badge>}<Badge variant="outline">{t('editor.readOnly')}</Badge></div>
            <F label={t('field.nodeName')}><Input readOnly value={d.node_name || ''} className="font-mono text-xs" /></F>
            <F label={t('field.reference')}><Input readOnly value={d.ref || ''} className="font-mono text-xs" /></F>
            <F label={t('field.source')}><pre className="h-72 w-[286px] overflow-auto rounded-md border bg-muted/50 p-2 text-[11px] leading-relaxed whitespace-pre">{d.source}</pre></F>
          </>}
          {selNode.type === 'retriever' && <>
            <RetrieverSettings kb={d.knowledge_base_id} topK={d.top_k} onKb={v => upd('knowledge_base_id', v)} onTopK={v => upd('top_k', v)} />
            <F label={t('field.queryTemplate', { field: '{{state.field}}' })}><Textarea rows={3} id="retriever-query" className="font-mono text-xs" value={d.query} onChange={e => upd('query', e.target.value)} /></F>
            <F label={t('field.outputField')}><Sel value={d.output_field} onChange={v => upd('output_field', v)} opts={fieldNames} /></F>
          </>}
          {selNode.type === 'mcp' && <>
            <McpSettings server={d.server_id} tool={d.tool} args={d.arguments} onChange={p => mark(selNode.id, p)} />
            <F label={t('field.outputField')}><Sel value={d.output_field} onChange={v => upd('output_field', v)} opts={fieldNames} /></F>
          </>}
          {selNode.type === 'subgraph' && <SubgraphSettings wid={wid} value={d.workflow_id} onChange={v => upd('workflow_id', v)} />}
          {selNode.type === 'join' && <p className="text-[11px] text-muted-foreground" id="join-hint">{t('editor.joinHint')}</p>}
          {selNode.type === 'condition' && <>
            <F label={t('editor.condField')}><Sel value={d.field} onChange={v => upd('field', v)} opts={fieldNames} /></F>
            <F label={t('editor.condDefault')}><Input value={d.default || ''} onChange={e => upd('default', e.target.value)} /></F>
            <p className="text-[11px] text-muted-foreground">{t('editor.condHint')}</p>
          </>}
          {!source && !PROTECTED.has(selNode.type!) && <div className="flex gap-2">
            <Button variant="outline" size="sm" id="duplicate-node" onClick={() => { const c = copySelection(nodes, edges, [selNode.id]); if (c) insert(c, 1) }}><CopyPlus />{t('clipboard.duplicate')}</Button>
            <Button variant="destructive" size="sm" id="delete-node" onClick={() => removeIds([selNode.id])}><Trash2 />{t('editor.deleteNode')}</Button></div>}
        </div>}
      </div></fieldset></ScrollArea>
    </aside>

    {/* Bottom run panel */}
    <section className="col-span-3 border-t min-h-0 flex flex-col">
      <Tabs value={tab} onValueChange={setTab} className="flex-1 min-h-0 flex flex-col gap-0">
        <div className="flex items-center gap-3 px-3 py-2 border-b">
          <TabsList><TabsTrigger value="input">{t('editor.tabInput')}</TabsTrigger><TabsTrigger value="logs">{t('editor.tabLogs')} {trace.spans.length > 0 && <Badge variant={trace.status === 'error' ? 'destructive' : 'secondary'} className="ml-1">{trace.spans.length}</Badge>}</TabsTrigger>
            <TabsTrigger value="history">{t('editor.tabHistory')}</TabsTrigger></TabsList>
          {errors.length > 0 && <Badge variant="destructive">{t('editor.errorsBadge', { count: errors.length })}</Badge>}
        </div>
        <TabsContent value="input" className="flex-1 min-h-0 p-3 flex gap-3">
          <Textarea id="run-input" className="font-mono text-xs flex-1 resize-none h-full" value={input} onChange={e => setInput(e.target.value)} />
          {errors.length > 0 && <ScrollArea className="w-1/2"><Alert variant="destructive" id="validation-errors"><AlertTriangle /><AlertTitle>{t('editor.errorsTitle', { count: errors.length })}</AlertTitle>
            <AlertDescription><ul className="list-disc pl-4 space-y-0.5 text-xs">{errors.map((e, i) => <li key={i} className="break-words">{e}</li>)}</ul></AlertDescription></Alert></ScrollArea>}
        </TabsContent>
        <TabsContent value="logs" className="flex-1 min-h-0">
          {trace.waiting?.runId && !running && <HumanPanel waiting={trace.waiting} onRespond={r => respond(trace.waiting!.runId!, r)} />}
          <RunTrace trace={trace} events={log as any} meta={traceMeta} selected={traceSel} onSelect={sp => setTraceSel(sp?.key ?? null)}
            replay={replay ?? undefined} onExitReplay={() => { setReplay(null); setLog([]); setTraceSel(null) }} />
        </TabsContent>
        <TabsContent value="history" className="flex-1 min-h-0">
          <ScrollArea className="h-full"><div className="p-3 space-y-1">
            {!history.length && <span className="text-muted-foreground text-xs">{t('editor.noRuns')}</span>}
            {history.map(h => <button key={h.id} data-testid="history-row" onClick={() => openRun(h)}
              className="w-full flex items-center gap-3 rounded-md px-2 py-1.5 text-left text-xs hover:bg-accent">
              <Badge variant={h.status === 'ok' ? 'success' : h.status === 'timeout' ? 'warning' : h.status === 'cancelled' || h.status === 'expired' ? 'secondary' : h.status === 'waiting' ? 'outline' : 'destructive'}>{t(`status.${h.status}`)}</Badge>
              <span className="text-muted-foreground w-20">{new Date(h.started * 1000).toLocaleTimeString(i18n.resolvedLanguage)}</span>
              <span className="font-mono text-muted-foreground">{h.id}</span>
              {h.source === 'api' && <Badge variant="outline" data-testid="history-source">API</Badge>}
              <Tip tip={h.version ? t('versions.runVersion', { n: h.version }) : t('versions.runUnsaved')}>
                <Badge variant="secondary" data-testid="history-version">{h.version ? `v${h.version}` : t('versions.unsaved')}</Badge></Tip>
              <span className="truncate">{JSON.stringify(h.input)}</span>
              <span className="ml-auto flex shrink-0 items-center gap-2 text-muted-foreground tabular-nums">
                {h.metrics && <span data-testid="history-tokens">{t('trace.tokens', { count: h.metrics.tokens })}</span>}
                {h.metrics && <span data-testid="history-cost">{fmtCost(h.metrics.cost_usd)}</span>}
                {h.metrics?.error_count > 0 && <Badge variant="destructive">{t('trace.errorCount', { count: h.metrics.error_count })}</Badge>}
                <span>{fmtMs(h.metrics?.duration_ms ?? (h.ended - h.started) * 1000)}</span>
                {h.trace_url && <ExternalLink className="size-3.5" aria-label={t('trace.openTrace')} />}{/* link itself is in the replayed timeline (no <a> inside a button) */}
              </span>
            </button>)}
          </div></ScrollArea>
        </TabsContent>
      </Tabs>
    </section>
  </div>
}
