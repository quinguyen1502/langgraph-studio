/** The editor's Chat tab (TASK-0085, REQ-0048 phase 1): chat with the saved workflow as a visitor would. Your chats
 *  on the left with "New chat"; the Builder / Visitor switch shows every step (builders always see full) or the steps
 *  the Chat settings give visitors. Runs use the saved workflow, like a chat trigger. */
import { useEffect, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { AlertCircle, MessageSquarePlus, Settings2, Trash2 } from 'lucide-react'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from '@/components/ui/alert-dialog'
import { Tip } from '@/components/tip'
import { api } from '@/lib/api'
import { fmtDate } from '@/lib/i18n'
import { useLoadWhen } from '@/lib/use-when'
import { cn } from '@/lib/utils'
import type { ChatSession, ChatSettings } from '@/lib/chat'
import { useChatRun, type ChatView } from './use-chat-run'
import { ChatThread } from './chat-thread'
import { ChatComposer } from './chat-composer'
import { ChatSettingsDialog } from './chat-settings-dialog'

export function ChatPanel({ wid, active, canConfigure, dirty }: { wid: string; active: boolean; canConfigure: boolean; dirty: boolean }) {
  const { t } = useTranslation()
  const [settings, setSettings] = useState<ChatSettings | null>(null); const [sessions, setSessions] = useState<ChatSession[]>([])
  const [sid, setSid] = useState<string | null>(null); const [view, setView] = useState<ChatView>('builder')
  const [err, setErr] = useState(''); const [cfg, setCfg] = useState(false); const [del, setDel] = useState<ChatSession | null>(null)
  const list = (pick?: string) => api<ChatSession[]>(`/api/workflows/${wid}/chat/sessions`).then(s => { setSessions(s); setSid(c => pick ?? (c && s.some(x => x.id === c) ? c : s[0]?.id ?? null)) })
  const chat = useChatRun(sid, view, () => { list().catch(() => {}) })   // titles and order change after a message
  useLoadWhen(active, () => { setErr(''); api<ChatSettings>(`/api/workflows/${wid}/chat`).then(setSettings).catch(e => setErr(e.message)); list().catch(e => setErr(e.message)) }, wid)
  const fresh = () => api<ChatSession>(`/api/workflows/${wid}/chat/sessions`, { method: 'POST' }).then(s => list(s.id)).catch(e => setErr(e.message))
  // the first message of a new chat creates it, then goes out once the chat is loaded
  const first = useRef(''); const { send: say, session } = chat
  const send = (text: string) => { if (sid) { say(text); return } first.current = text
    api<ChatSession>(`/api/workflows/${wid}/chat/sessions`, { method: 'POST' }).then(s => list(s.id)).catch(e => { first.current = ''; setErr(e.message) }) }
  useEffect(() => { if (first.current && sid && session?.id === sid) { const x = first.current; first.current = ''; say(x) } }, [sid, session, say])
  const remove = (s: ChatSession) => api(`/api/chat/sessions/${s.id}`, { method: 'DELETE' }).then(() => { if (sid === s.id) setSid(null); list() }).catch(e => setErr(e.message))
  const mode = view === 'builder' ? 'full' : chat.session?.steps_mode ?? settings?.steps ?? 'labels'
  const off = settings && !settings.enabled
  return <div className="flex h-full min-h-0" id="chat-panel">
    <aside className="flex w-56 shrink-0 flex-col border-r">
      <div className="p-2"><Button size="sm" variant="outline" className="w-full justify-start" id="chat-new" disabled={!!off} onClick={fresh}><MessageSquarePlus />{t('chat.new')}</Button></div>
      <ScrollArea className="min-h-0 flex-1"><nav className="space-y-0.5 px-2 pb-2" aria-label={t('chat.sessions')}>
        {!sessions.length && <p className="px-2 py-1 text-xs text-muted-foreground">{t('chat.noSessions')}</p>}
        {sessions.map(s => <div key={s.id} className={cn('group flex items-center gap-1 rounded-md hover:bg-accent', s.id === sid && 'bg-accent')}>
          <button data-testid="chat-session" aria-current={s.id === sid || undefined} onClick={() => setSid(s.id)} className="min-w-0 flex-1 px-2 py-1.5 text-left">
            <div className="truncate text-xs font-medium">{s.title || t('chat.untitled')}</div>
            <div className="truncate text-[11px] text-muted-foreground tabular-nums">{fmtDate(s.updated)}</div></button>
          <Button size="icon-xs" variant="ghost" className="opacity-0 group-hover:opacity-100 focus-visible:opacity-100" aria-label={t('chat.delete')} data-testid="chat-delete" onClick={() => setDel(s)}><Trash2 /></Button>
        </div>)}
      </nav></ScrollArea>
    </aside>
    <div className="flex min-w-0 flex-1 flex-col">
      <div className="flex items-center gap-2 border-b px-3 py-1.5">
        <Tabs value={view} onValueChange={v => setView(v as ChatView)}><TabsList className="h-7">
          <TabsTrigger value="builder" id="chat-view-builder" className="text-xs">{t('chat.viewBuilder')}</TabsTrigger>
          <TabsTrigger value="visitor" id="chat-view-visitor" className="text-xs">{t('chat.viewVisitor')}</TabsTrigger></TabsList></Tabs>
        <span className="truncate text-xs text-muted-foreground" id="chat-mode-hint">{t(`chat.stepsHint.${mode}`)}</span>
        {dirty && <span className="truncate text-xs text-warning" id="chat-unsaved">{t('chat.unsaved')}</span>}
        {canConfigure && <Tip tip={t('chat.settings.title')}><Button size="icon-sm" variant="ghost" className="ml-auto" id="chat-settings-btn" aria-label={t('chat.settings.title')} onClick={() => setCfg(true)}><Settings2 /></Button></Tip>}
      </div>
      {(err || chat.error) && <Alert variant="destructive" className="m-3 w-auto"><AlertCircle /><AlertDescription id="chat-error-banner">{err || chat.error}</AlertDescription></Alert>}
      {off ? <div className="m-auto max-w-sm space-y-3 p-6 text-center" id="chat-off">
          <p className="text-sm text-muted-foreground">{t('chat.off')}</p>
          {canConfigure && <Button size="sm" id="chat-turn-on" onClick={() => setCfg(true)}><Settings2 />{t('chat.settings.open')}</Button>}</div>
        : settings && <ChatThread turns={chat.session?.turns ?? []} mode={mode} settings={settings} events={chat.events} trace={chat.trace}
            pending={chat.pending} running={chat.running} onAnswer={chat.answer} />}
      {!off && <ChatComposer disabled={!settings} running={chat.running} onSend={send} onStop={chat.cancel} />}
    </div>
    <ChatSettingsDialog wid={wid} open={cfg} onOpenChange={setCfg} onSaved={setSettings} />
    <AlertDialog open={!!del} onOpenChange={o => { if (!o) setDel(null) }}><AlertDialogContent>
      <AlertDialogHeader><AlertDialogTitle>{t('chat.deleteTitle')}</AlertDialogTitle><AlertDialogDescription>{t('chat.deleteBody', { title: del?.title || t('chat.untitled') })}</AlertDialogDescription></AlertDialogHeader>
      <AlertDialogFooter><AlertDialogCancel>{t('common.cancel')}</AlertDialogCancel>
        <AlertDialogAction asChild><Button variant="destructive" id="chat-delete-confirm" onClick={() => { if (del) remove(del); setDel(null) }}>{t("common.delete")}</Button></AlertDialogAction></AlertDialogFooter>
    </AlertDialogContent></AlertDialog>
  </div>
}
