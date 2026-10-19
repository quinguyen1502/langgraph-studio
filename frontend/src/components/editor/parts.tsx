import { type Edge } from '@xyflow/react'
import { Trash2, type LucideIcon, CopyPlus, ArrowRight, Copy, Scissors, ArrowLeft } from 'lucide-react'
import { ContextMenuItem, ContextMenuSeparator, ContextMenuSub, ContextMenuSubContent, ContextMenuSubTrigger } from '@/components/ui/context-menu'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { useTranslation } from 'react-i18next'
import { PROTECTED } from '@/lib/graph-ops'
import { META, INSERTABLE } from './meta'

export function Sel({ value, onChange, opts, ph }: { value?: string; onChange: (v: string) => void; opts: string[]; ph?: string }) {
  const { t } = useTranslation()
  return <Select value={value || undefined} onValueChange={onChange}>
      <SelectTrigger className="w-full"><SelectValue placeholder={ph || t('common.choose')} /></SelectTrigger>
      <SelectContent>{opts.filter(Boolean).map(o => <SelectItem key={o} value={o}>{o}</SelectItem>)}</SelectContent>
    </Select>
}
export const F = ({ label, children }: { label: string; children: React.ReactNode }) => <div className="space-y-1.5"><Label className="text-xs text-muted-foreground">{label}</Label>{children}</div>

export function InsertMenu({ id, label, icon: Icon, onPick }: { id: string; label: string; icon: LucideIcon; onPick: (type: string) => void }) {
  return <ContextMenuSub>
    <ContextMenuSubTrigger id={`${id}-insert`}><Icon />{label}</ContextMenuSubTrigger>
    <ContextMenuSubContent>
      {INSERTABLE.map(type => { const I = META[type].icon; return <ContextMenuItem key={type} id={`${id}-insert-${type}`} onSelect={() => onPick(type)}><I />{META[type].label}</ContextMenuItem> })}
    </ContextMenuSubContent>
  </ContextMenuSub>
}

export function NodeMenu({ id, type, edges, canDelete, insert, onCopy, onCut, onDuplicate, onDelete }: {
  id: string; type?: string; edges: Edge[]; canDelete: boolean
  insert: (type: string, where: { dir: 'before' | 'after'; anchor: string }) => void
  onCopy: () => void; onCut: () => void; onDuplicate: () => void; onDelete: () => void
}) {
  const { t } = useTranslation()
  const locked = PROTECTED.has(type ?? '')
  const ins = edges.filter(e => e.target === id).length
  const outs = edges.filter(e => e.source === id).length
  if (type === 'note') return <>
    <ContextMenuItem id="copy-node" onSelect={onCopy}><Copy />{t('editor.copyNode')}</ContextMenuItem>
    <ContextMenuItem id="cut-node" onSelect={onCut}><Scissors />{t('editor.cutNode')}</ContextMenuItem>
    <ContextMenuItem id="duplicate-node" onSelect={onDuplicate}><CopyPlus />{t('clipboard.duplicate')}</ContextMenuItem>
    <ContextMenuSeparator />
    <ContextMenuItem id="delete-note" variant="destructive" onSelect={onDelete}><Trash2 />{t('editor.deleteNote')}</ContextMenuItem>
  </>
  return <>
    {type !== 'start' && ins <= 1 && <InsertMenu id="before" label={t('editor.insertBefore')} icon={ArrowLeft} onPick={tp => insert(tp, { dir: 'before', anchor: id })} />}
    {type !== 'end' && outs <= 1 && <InsertMenu id="after" label={t('editor.insertAfter')} icon={ArrowRight} onPick={tp => insert(tp, { dir: 'after', anchor: id })} />}
    {!locked && <>
      <ContextMenuSeparator />
      <ContextMenuItem id="copy-node" onSelect={onCopy}><Copy />{t('editor.copyNode')}</ContextMenuItem>
      <ContextMenuItem id="cut-node" onSelect={onCut}><Scissors />{t('editor.cutNode')}</ContextMenuItem>
      <ContextMenuItem id="duplicate-node" onSelect={onDuplicate}><CopyPlus />{t('clipboard.duplicate')}</ContextMenuItem>
    </>}
    {canDelete && <>
      <ContextMenuSeparator />
      <ContextMenuItem id="delete-node" variant="destructive" onSelect={onDelete}><Trash2 />{t('editor.deleteNode')}</ContextMenuItem>
    </>}
  </>
}
