import { useState } from 'react'
import { Check, ChevronRight, Copy } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible'
import { cn } from '@/lib/utils'

export function CopyButton({ value, className }: { value: any; className?: string }) {
  const [ok, setOk] = useState(false)
  const copy = async () => {
    const txt = typeof value === 'string' ? value : JSON.stringify(value, null, 2)
    try { await navigator.clipboard.writeText(txt) } catch { /* clipboard may be unavailable (http) */ }
    setOk(true); setTimeout(() => setOk(false), 1200)
  }
  return <Button variant="ghost" size="icon" className={cn('size-6', className)} onClick={copy} aria-label="Copy JSON" title="Copy JSON">{ok ? <Check className="size-3.5" /> : <Copy className="size-3.5" />}</Button>
}

function Leaf({ v }: { v: any }) {
  if (v === null) return <span className="text-muted-foreground">null</span>
  if (typeof v === 'string') return <span className="text-success break-all whitespace-pre-wrap">"{v}"</span>
  if (typeof v === 'number') return <span className="text-info">{v}</span>
  if (typeof v === 'boolean') return <span className="text-warning">{String(v)}</span>
  return <span>{String(v)}</span>
}

function Node({ k, v, depth }: { k?: string; v: any; depth: number }) {
  const isObj = v !== null && typeof v === 'object'
  const [open, setOpen] = useState(depth < 2)
  const keyEl = k != null && <span className="text-foreground/80">{k}: </span>
  if (!isObj) return <div className="pl-4">{keyEl}<Leaf v={v} /></div>
  const entries = Array.isArray(v) ? v.map((x, i) => [String(i), x] as const) : Object.entries(v)
  const [o, c] = Array.isArray(v) ? ['[', ']'] : ['{', '}']
  return <Collapsible open={open} onOpenChange={setOpen} className={cn(depth > 0 && 'pl-4')}>
    <CollapsibleTrigger asChild><Button variant="ghost" size="icon" className="size-4 -ml-4 align-middle text-muted-foreground" aria-label={open ? 'Thu gọn' : 'Mở rộng'}>
      <ChevronRight className={cn('size-3.5 transition-transform', open && 'rotate-90')} /></Button></CollapsibleTrigger>
    {keyEl}<span className="text-muted-foreground">{o}{!open && <> {entries.length} {Array.isArray(v) ? 'items' : 'keys'} {c}</>}</span>
    <CollapsibleContent>{entries.map(([kk, vv]) => <Node key={kk} k={kk} v={vv} depth={depth + 1} />)}<div className="text-muted-foreground">{c}</div></CollapsibleContent>
  </Collapsible>
}

export function JsonView({ value, className }: { value: any; className?: string }) {
  return <div className={cn('relative rounded-md border bg-muted/30 p-2 pl-6 font-mono text-[11px] leading-5', className)}>
    <CopyButton value={value} className="absolute right-1 top-1" />
    {value === undefined ? <span className="text-muted-foreground">(không có dữ liệu)</span> : <Node v={value} depth={0} />}
  </div>
}
