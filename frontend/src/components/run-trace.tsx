import { useTranslation } from 'react-i18next'
import { useState } from 'react'
import { AlertTriangle, Ban, CheckCircle2, Clock, Hand, TimerOff, Coins, DollarSign, ExternalLink, Layers, Loader2, X, XCircle, type LucideIcon } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Switch } from '@/components/ui/switch'
import { Label } from '@/components/ui/label'
import { Separator } from '@/components/ui/separator'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { JsonView } from '@/components/json-view'
import { fmtCost, fmtMs, stateDiff, type RunEvent, type Span, type Trace } from '@/lib/trace'
import { cn } from '@/lib/utils'

type Meta = (type: string) => { icon: LucideIcon; color: string; label: string }

const StatusIcon = ({ s, className }: { s: Span['status'] | Trace['status']; className?: string }) =>
  s === 'running' ? <Loader2 className={cn('size-4 animate-spin text-warning', className)} />
  : s === 'error' ? <XCircle className={cn('size-4 text-destructive', className)} />
  : s === 'cancelled' ? <Ban className={cn('size-4 text-muted-foreground', className)} />
  : s === 'expired' ? <TimerOff className={cn('size-4 text-muted-foreground', className)} />
  : s === 'timeout' ? <TimerOff className={cn('size-4 text-warning', className)} />
  : s === 'waiting' ? <Hand className={cn('size-4 text-node-human', className)} />
  : s === 'idle' ? <Clock className={cn('size-4 text-muted-foreground', className)} />
  : <CheckCircle2 className={cn('size-4 text-success', className)} />


function Summary({ trace, replay, onExitReplay, raw, setRaw }: { trace: Trace; replay?: string; onExitReplay?: () => void; raw: boolean; setRaw: (b: boolean) => void }) {
  const { t } = useTranslation()
  return <div id="trace-summary" data-status={trace.status} className={cn('flex items-center gap-3 border-b px-3 py-1.5 text-xs', (trace.status === 'error') && 'bg-destructive/5', trace.status === 'timeout' && 'bg-warning/10', trace.status === 'cancelled' && 'bg-muted')}>
    <span className="flex items-center gap-1.5 font-medium"><StatusIcon s={trace.status} />{t(`trace.${trace.status}`)}</span>
    <Separator orientation="vertical" className="h-4" />
    <span className="flex items-center gap-1 text-muted-foreground"><Clock className="size-3.5" />{fmtMs(trace.total)}</span>
    <span className="flex items-center gap-1 text-muted-foreground"><Layers className="size-3.5" />{t('trace.steps', { count: trace.spans.length })}</span>
    {trace.tokens != null && <span id="trace-tokens" className="flex items-center gap-1 text-muted-foreground"><Coins className="size-3.5" />{t('trace.tokens', { count: trace.tokens })}</span>}
    {trace.metrics && <span id="trace-cost" className="flex items-center gap-1 text-muted-foreground"><DollarSign className="size-3.5" />{fmtCost(trace.metrics.cost_usd)}</span>}
    {trace.metrics && trace.metrics.error_count > 0 && <Badge variant="destructive" id="trace-error-count">{t('trace.errorCount', { count: trace.metrics.error_count })}</Badge>}
    {trace.traceUrl && <Button asChild variant="ghost" size="sm" className="h-6 gap-1 px-2 text-xs" id="trace-link"><a href={trace.traceUrl} target="_blank" rel="noreferrer"><ExternalLink className="size-3.5" />{t('trace.openTrace')}</a></Button>}
    {replay && <Badge variant="outline" className="gap-1">Replay {replay}{onExitReplay && <Button variant="ghost" size="icon" className="size-4" aria-label={t('trace.exitReplay')} onClick={onExitReplay}><X className="size-3" /></Button>}</Badge>}
    <div className="ml-auto flex items-center gap-2">
      <Switch id="raw-toggle" size="sm" checked={raw} onCheckedChange={setRaw} />
      <Label htmlFor="raw-toggle" className="text-xs font-normal text-muted-foreground">{t('trace.rawEvents')}</Label></div>
  </div>
}

function Row({ s, trace, meta, selected, onClick }: { s: Span; trace: Trace; meta: Meta; selected: boolean; onClick: () => void }) {
  const { t } = useTranslation(); const m = meta(s.type); const I = m.icon
  const total = Math.max(trace.total || 0, 1); const t0 = trace.start ?? s.start
  const left = Math.min(100, ((s.start - t0) * 1000 / total) * 100)
  const width = Math.max(1.5, Math.min(100 - left, ((s.duration ?? ((s.end ?? trace.end ?? s.start) - s.start) * 1000) / total) * 100))
  return <button type="button" onClick={onClick} data-span={s.key} aria-selected={selected}
    className={cn('trace-row w-full grid grid-cols-[18px_minmax(0,1fr)_72px_minmax(80px,30%)] items-center gap-2 px-3 py-1 text-left text-xs hover:bg-accent/60 border-l-2 border-transparent',
      selected && 'bg-accent border-l-primary', s.status === 'error' && 'bg-destructive/5 hover:bg-destructive/10')}>
    <StatusIcon s={s.status} className="size-3.5" />
    <span className="flex items-center gap-1.5 min-w-0">
      <span className={cn('rounded p-0.5', m.color)}><I className="size-3" /></span>
      <span className={cn('truncate font-medium shrink-0 max-w-[45%]', s.status === 'error' && 'text-destructive')}>{s.label}</span>
      {s.iter > 1 && <Badge variant="secondary" className="h-4 px-1 text-[10px]">#{s.iter}</Badge>}
      <span className="truncate shrink-0 max-w-[25%] text-muted-foreground font-mono text-[10px]">{s.node}</span>
      {s.tokens != null && <Tooltip><TooltipTrigger asChild><span className="text-muted-foreground text-[10px]" data-testid="span-tokens">· {t('trace.tokensShort', { count: s.tokens })}{s.cost ? ` · ${fmtCost(s.cost)}` : ''}</span></TooltipTrigger>
        <TooltipContent>{t('trace.usageDetail', { model: s.usage?.model ?? '—', tin: s.usage?.tokens_in ?? 0, tout: s.usage?.tokens_out ?? 0, cost: fmtCost(s.cost) })}{s.usage?.estimated ? ` ${t('trace.estimated')}` : ''}</TooltipContent></Tooltip>}
      {s.error && <Tooltip><TooltipTrigger asChild><span className="truncate min-w-0 text-destructive text-[11px]">— {s.error}</span></TooltipTrigger>
        <TooltipContent className="max-w-md break-all">{s.error}</TooltipContent></Tooltip>}
    </span>
    <span className="text-right tabular-nums text-muted-foreground">{s.status === 'running' && s.duration == null ? '…' : fmtMs(s.duration)}</span>
    <span className="relative h-1.5 rounded-full bg-muted overflow-hidden">
      <span className={cn('absolute inset-y-0 rounded-full', s.status === 'error' ? 'bg-destructive' : s.status === 'running' ? 'bg-warning animate-pulse' : 'bg-primary/70')} style={{ left: `${left}%`, width: `${width}%` }} />
    </span>
  </button>
}

function DiffView({ s }: { s: Span }) {
  const { t } = useTranslation(); const rows = stateDiff(s.input, s.output)
  if (!rows.length) return <p className="text-muted-foreground text-xs p-2">{t('trace.noDiff')}</p>
  const v = (x: any) => typeof x === 'string' ? x : JSON.stringify(x)
  return <div className="rounded-md border font-mono text-[11px] divide-y" id="trace-diff">
    {rows.map(r => <div key={r.key} data-kind={r.kind} className={cn('grid grid-cols-[16px_120px_1fr] gap-2 px-2 py-1',
      r.kind === 'added' && 'bg-success/10', r.kind === 'changed' && 'bg-warning/10', r.kind === 'removed' && 'bg-destructive/10', r.kind === 'same' && 'text-muted-foreground')}>
      <span className={cn(r.kind === 'added' && 'text-success', r.kind === 'changed' && 'text-warning', r.kind === 'removed' && 'text-destructive')}>{{ added: '+', changed: '~', removed: '−', same: ' ' }[r.kind]}</span>
      <span className="truncate font-semibold" title={r.key}>{r.key}</span>
      <span className="break-all whitespace-pre-wrap">{r.kind === 'changed' ? <><span className="line-through opacity-60">{v(r.before)}</span>{' → '}<span>{v(r.after)}</span></> : v(r.kind === 'removed' ? r.before : r.after)}</span>
    </div>)}
  </div>
}

function Detail({ s, meta, onClose }: { s: Span; meta: Meta; onClose: () => void }) {
  const { t } = useTranslation(); const m = meta(s.type); const I = m.icon
  const [tab, setTab] = useState(s.status === 'error' ? 'output' : 'diff')
  return <div className="w-[46%] min-w-80 border-l flex flex-col min-h-0" id="trace-detail">
    <div className="flex items-center gap-2 px-3 py-1.5 border-b text-xs">
      <span className={cn('rounded p-0.5', m.color)}><I className="size-3.5" /></span>
      <span className="font-medium truncate">{s.label}{s.iter > 1 && ` #${s.iter}`}</span>
      <Badge variant="outline" className="h-4 px-1 text-[10px]">{m.label}</Badge>
      <span className="text-muted-foreground tabular-nums">{fmtMs(s.duration)}</span>
      <Button variant="ghost" size="icon" className="size-6 ml-auto" onClick={onClose} aria-label={t('trace.closeDetail')}><X className="size-3.5" /></Button>
    </div>
    <Tabs value={tab} onValueChange={setTab} className="flex-1 min-h-0 flex flex-col gap-0">
      <TabsList className="mx-3 mt-1.5 h-7">{['input', 'output', 'diff', 'raw'].map(k => <TabsTrigger key={k} value={k} className="text-xs h-5 px-2">{t(`trace.${k}`)}</TabsTrigger>)}</TabsList>
      <ScrollArea className="flex-1 min-h-0"><div className="p-3 pt-2">
        {s.error && <Alert variant="destructive" className="mb-2 py-2 text-xs"><AlertTriangle /><AlertDescription className="break-all text-xs">{s.error}</AlertDescription></Alert>}
        <TabsContent value="input"><JsonView value={s.input} /></TabsContent>
        <TabsContent value="output"><JsonView value={s.output} /></TabsContent>
        <TabsContent value="diff"><DiffView s={s} /></TabsContent>
        <TabsContent value="raw"><JsonView value={s.events} /></TabsContent>
      </div></ScrollArea>
    </Tabs>
  </div>
}

export function RunTrace({ trace, events, meta, selected, onSelect, replay, onExitReplay }: {
  trace: Trace; events: RunEvent[]; meta: Meta; selected: string | null; onSelect: (s: Span | null) => void; replay?: string; onExitReplay?: () => void
}) {
  const { t } = useTranslation(); const [raw, setRaw] = useState(false)
  const sel = trace.spans.find(s => s.key === selected) || null
  if (!events.length) return <div className="p-3 text-xs text-muted-foreground">{t('trace.empty')}</div>
  return <div className="h-full flex flex-col min-h-0">
    <Summary trace={trace} replay={replay} onExitReplay={onExitReplay} raw={raw} setRaw={setRaw} />
    <div className="flex-1 min-h-0 flex">
      <ScrollArea className="flex-1 min-h-0"><div className="py-1" id="trace-timeline">
        {raw ? <div className="px-3 font-mono text-[11px] space-y-0.5" id="raw-events">{events.map((e, i) => <div key={i} className={cn('break-all', e.type === 'error' && 'text-destructive')}><span className="text-muted-foreground">{i}</span> {JSON.stringify(e)}</div>)}</div>
        : <>{trace.spans.map(s => <Row key={s.key} s={s} trace={trace} meta={meta} selected={s.key === selected} onClick={() => onSelect(s.key === selected ? null : s)} />)}
          {trace.errors.length > 0 && !trace.spans.some(s => s.error) && <Alert variant={trace.status === 'timeout' ? 'default' : 'destructive'} id="trace-run-error" className={cn('mx-3 my-1 w-auto py-2', trace.status === 'timeout' && 'border-warning/40 bg-warning/10 text-warning')}>{trace.status === 'timeout' ? <TimerOff /> : <AlertTriangle />}<AlertDescription className="text-xs">{trace.errors.join('; ')}</AlertDescription></Alert>}
          {trace.status === 'cancelled' && <Alert className="mx-3 my-1 w-auto py-2" id="trace-cancelled"><Ban /><AlertDescription className="text-xs">{t(events.some(e => e.reason === 'disconnect') ? 'trace.cancelledDisconnect' : 'trace.cancelledMsg')}</AlertDescription></Alert>}
          {trace.status === 'ok' && <div className="px-3 pt-1 text-[11px] text-muted-foreground" id="trace-done">{t('trace.done', { count: Object.keys(trace.final || {}).length })}</div>}</>}
      </div></ScrollArea>
      {sel && !raw && <Detail key={sel.key} s={sel} meta={meta} onClose={() => onSelect(null)} />}
    </div>
  </div>
}
