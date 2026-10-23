/** The message box (TASK-0085), after the AI Elements Prompt Input pattern: Enter sends, Shift+Enter is a new line,
 *  a counter appears near the limit, and Stop cancels the run. Attachments come later (REQ-0048 phase 2). */
import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { ArrowUp, Square } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { MAX_MESSAGE } from '@/lib/chat'

export function ChatComposer({ disabled, running, onSend, onStop, hint }: { disabled: boolean; running: boolean; onSend: (text: string) => void; onStop: () => void; hint?: string }) {
  const { t } = useTranslation(); const [text, setText] = useState('')
  const ok = !!text.trim() && text.length <= MAX_MESSAGE && !disabled && !running
  const send = () => { if (!ok) return; onSend(text.trim()); setText('') }
  return <div className="border-t p-3"><div className="mx-auto max-w-3xl rounded-xl border bg-background focus-within:ring-3 focus-within:ring-ring/50">
    <Textarea id="chat-input" aria-label={t('chat.message')} placeholder={hint ?? t('chat.placeholder')} rows={1} disabled={disabled}
      className="max-h-40 min-h-10 resize-none border-0 bg-transparent shadow-none focus-visible:ring-0 dark:bg-transparent" value={text}
      onChange={e => setText(e.target.value)} onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey && !e.nativeEvent.isComposing) { e.preventDefault(); send() } }} />
    <div className="flex items-center justify-end gap-2 px-2 pb-2">
      {text.length > MAX_MESSAGE * 0.9 && <span className={text.length > MAX_MESSAGE ? 'text-xs text-destructive' : 'text-xs text-muted-foreground'} id="chat-count">{text.length}/{MAX_MESSAGE}</span>}
      {running ? <Button size="icon-sm" variant="outline" id="chat-stop" aria-label={t('chat.stop')} onClick={onStop}><Square /></Button>
        : <Button size="icon-sm" id="chat-send" aria-label={t('chat.send')} disabled={!ok} onClick={send}><ArrowUp /></Button>}
    </div>
  </div></div>
}
