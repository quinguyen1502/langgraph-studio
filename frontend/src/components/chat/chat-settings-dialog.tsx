/** A workflow's Chat settings (TASK-0085, REQ-0048): on/off, who may chat (studio now; anonymous and signed-in are
 *  reserved), the input / reply / messages fields, the memory window, which steps visitors see and how long chats are kept. */
import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { AlertCircle, Save } from 'lucide-react'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { api, ApiError } from '@/lib/api'
import { ACCESS, ACCESS_RESERVED, STEPS, type ChatSettings } from '@/lib/chat'
import { useLoadWhen } from '@/lib/use-when'

type Field = { name: string; type: string }
const NONE = '__none'

export function ChatSettingsDialog({ wid, open, onOpenChange, onSaved }: { wid?: string; open: boolean; onOpenChange: (v: boolean) => void; onSaved?: (s: ChatSettings) => void }) {
  const { t } = useTranslation(); const [v, setV] = useState<ChatSettings | null>(null); const [fields, setFields] = useState<Field[]>([])
  const [err, setErr] = useState(''); const [bad, setBad] = useState(''); const [busy, setBusy] = useState(false)
  useLoadWhen(open, () => {
    setErr(''); setBad('')
    Promise.all([api<ChatSettings>(`/api/workflows/${wid}/chat`), api<{ state?: Field[] }>(`/api/workflows/${wid}`)])
      .then(([s, wf]) => { setV(s); setFields(wf.state || []) }).catch(e => setErr(e.message))
  })
  const set = (p: Partial<ChatSettings>) => setV(x => x && { ...x, ...p })
  const save = () => { if (!v) return; setBusy(true); setErr(''); setBad('')
    const { slug: _slug, ...body } = v
    api<ChatSettings>(`/api/workflows/${wid}/chat`, { method: 'PUT', json: body }).then(s => { setV(s); onSaved?.(s); onOpenChange(false) })
      .catch(e => { setErr(e.message); if (e instanceof ApiError) setBad(e.details?.field ?? '') }).finally(() => setBusy(false)) }
  const names = (pred: (f: Field) => boolean) => fields.filter(pred).map(f => f.name)
  const pick = (id: keyof ChatSettings, opts: string[], none = false) => <Select value={(v?.[id] as string) || (none ? NONE : '')} onValueChange={x => set({ [id]: x === NONE ? '' : x } as any)}>
    <SelectTrigger className="w-full" id={`chat-${id}`} aria-invalid={bad === id || undefined}><SelectValue placeholder={t('chat.settings.pickField')} /></SelectTrigger>
    <SelectContent>{none && <SelectItem value={NONE}>{t('chat.settings.noMemory')}</SelectItem>}{opts.map(o => <SelectItem key={o} value={o}>{o}</SelectItem>)}</SelectContent></Select>
  const row = (id: string, label: string, hint: string | null, control: React.ReactNode) => <div className="grid gap-1.5">
    <Label htmlFor={`chat-${id}`}>{label}</Label>{control}{hint && <p className="text-xs text-muted-foreground">{hint}</p>}</div>
  return <Dialog open={open} onOpenChange={onOpenChange}>
    <DialogContent className="max-h-[85vh] overflow-y-auto sm:max-w-lg" id="chat-settings">
      <DialogHeader><DialogTitle>{t('chat.settings.title')}</DialogTitle><DialogDescription>{t('chat.settings.desc')}</DialogDescription></DialogHeader>
      {err && <Alert variant="destructive"><AlertCircle /><AlertDescription id="chat-settings-error">{err}</AlertDescription></Alert>}
      {v && <div className="grid gap-4">
        <div className="flex items-center justify-between gap-3 rounded-lg border p-3">
          <div className="grid gap-0.5"><Label htmlFor="chat-enabled">{t('chat.settings.enabled')}</Label><p className="text-xs text-muted-foreground">{t('chat.settings.enabledHint')}</p></div>
          <Switch id="chat-enabled" checked={v.enabled} onCheckedChange={enabled => set({ enabled })} /></div>
        {row('access', t('chat.settings.access'), t('chat.settings.accessHint'), <Select value={v.access} onValueChange={access => set({ access })}>
          <SelectTrigger className="w-full" id="chat-access"><SelectValue /></SelectTrigger>
          <SelectContent>{ACCESS.map(a => <SelectItem key={a} value={a}>{t(`chat.access.${a}`)}</SelectItem>)}
            {ACCESS_RESERVED.map(a => <SelectItem key={a} value={a} disabled>{t(`chat.access.${a}`)} <Badge variant="secondary" className="ml-1">{t('chat.settings.later')}</Badge></SelectItem>)}</SelectContent></Select>)}
        <div className="grid grid-cols-2 gap-3">
          {row('input_field', t('chat.settings.inputField'), null, pick('input_field', names(f => f.type === 'string' || f.type === 'list')))}
          {row('reply_field', t('chat.settings.replyField'), null, pick('reply_field', names(() => true)))}
        </div>
        {row('messages_field', t('chat.settings.messagesField'), t('chat.settings.messagesHint'), pick('messages_field', names(f => f.type === 'list' && f.name !== v.input_field), true))}
        <div className="grid grid-cols-2 gap-3">
          {row('max_turns', t('chat.settings.maxTurns'), t('chat.settings.maxTurnsHint'), <Input id="chat-max_turns" type="number" min={1} max={50} disabled={!v.messages_field}
            aria-invalid={bad === 'max_turns' || undefined} value={v.max_turns} onChange={e => set({ max_turns: Number(e.target.value) })} />)}
          {row('retention_days', t('chat.settings.retention'), t('chat.settings.retentionHint'), <Input id="chat-retention_days" type="number" min={1} max={3650}
            aria-invalid={bad === 'retention_days' || undefined} value={v.retention_days} onChange={e => set({ retention_days: Number(e.target.value) })} />)}
        </div>
        {row('steps', t('chat.settings.steps'), t('chat.settings.stepsHint'), <Select value={v.steps} onValueChange={steps => set({ steps: steps as ChatSettings['steps'] })}>
          <SelectTrigger className="w-full" id="chat-steps"><SelectValue /></SelectTrigger>
          <SelectContent>{STEPS.map(s => <SelectItem key={s} value={s}>{t(`chat.steps.${s}`)}</SelectItem>)}</SelectContent></Select>)}
      </div>}
      <DialogFooter><Button id="chat-settings-save" disabled={!v || busy} onClick={save}><Save />{t('common.save')}</Button></DialogFooter>
    </DialogContent>
  </Dialog>
}
