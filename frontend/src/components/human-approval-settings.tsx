import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { MessageSquareShare } from 'lucide-react'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Separator } from '@/components/ui/separator'
import type { Channels } from '@/components/approval-channels-dialog'

export type Approval = { channel?: string; target?: string; approvers?: string[] }

/** Per-Human-node approval channel (TASK-0022): where the Approve/Reject message goes and who may answer it. */
export function HumanApprovalSettings({ value, channels, onChange }: { value?: Approval; channels: Channels | null; onChange: (v: Approval) => void }) {
  const { t } = useTranslation(); const v = value || {}
  const set = (patch: Approval) => onChange({ ...v, ...patch })
  const [raw, setRaw] = useState((v.approvers || []).join(', '))  // free text while typing; the list is what is saved
  const kind = channels?.kinds.find(k => k.kind === v.channel)
  return <div className="space-y-3" id="human-approval">
    <Separator />
    <div className="flex items-center gap-2 text-xs font-semibold uppercase text-muted-foreground"><MessageSquareShare className="size-3.5" />{t('approvals.node.title')}</div>
    <div className="space-y-1.5"><Label className="text-xs text-muted-foreground">{t('approvals.node.channel')}</Label>
      <Select value={v.channel || 'none'} onValueChange={c => set({ channel: c === 'none' ? '' : c })}>
        <SelectTrigger className="w-full" id="approval-channel"><SelectValue /></SelectTrigger>
        <SelectContent><SelectItem value="none">{t('approvals.node.studioOnly')}</SelectItem>
          {(channels?.kinds || []).map(k => <SelectItem key={k.kind} value={k.kind}>{t(`approvals.kind.${k.kind}`)}{!k.channel && ` · ${t('approvals.notConnected')}`}</SelectItem>)}</SelectContent></Select></div>
    {v.channel && <>
      {kind && !kind.channel && <Alert id="approval-not-connected"><AlertDescription className="text-xs">{t('approvals.node.connectFirst')}</AlertDescription></Alert>}
      <div className="space-y-1.5"><Label htmlFor="approval-target" className="text-xs text-muted-foreground">{t(`approvals.node.target.${v.channel}`)}</Label>
        <Input id="approval-target" className="font-mono text-xs" value={v.target || ''} placeholder={t(`approvals.node.targetPh.${v.channel}`)} onChange={e => set({ target: e.target.value })} /></div>
      <div className="space-y-1.5"><Label htmlFor="approval-approvers" className="text-xs text-muted-foreground">{t('approvals.node.approvers')}</Label>
        <Input id="approval-approvers" className="text-xs" value={raw} placeholder="lead@example.com, ops@example.com"
          onChange={e => { setRaw(e.target.value); set({ approvers: e.target.value.split(',').map(x => x.trim()).filter(Boolean) }) }} />
        <p className="text-xs text-muted-foreground">{t('approvals.node.approversHelp')}</p></div>
    </>}
  </div>
}
