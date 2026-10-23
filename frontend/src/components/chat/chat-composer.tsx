/** The message box (TASK-0085), built as the shadcn Prompt Input pattern: a form with an Input Group, its textarea and
 *  a block-end addon with the send button (Stop while a run goes). Enter sends, Shift+Enter adds a line. A counter
 *  shows near the limit. Attachments come in phase 2 (REQ-0048). */
import { useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { ArrowUp, Square } from 'lucide-react'
import { InputGroup, InputGroupAddon, InputGroupButton, InputGroupText, InputGroupTextarea } from '@/components/ui/input-group'
import { MAX_MESSAGE } from '@/lib/chat'

export function ChatComposer({ disabled, running, onSend, onStop, placeholder }: { disabled: boolean; running: boolean; onSend: (text: string) => void; onStop: () => void; placeholder?: string }) {
  const { t } = useTranslation(); const [text, setText] = useState(''); const form = useRef<HTMLFormElement>(null)
  const canSend = !!text.trim() && text.length <= MAX_MESSAGE && !disabled && !running
  const submit = (e: React.FormEvent) => { e.preventDefault(); if (!canSend) return; onSend(text.trim()); setText('') }
  return <form ref={form} onSubmit={submit} className="mx-auto w-full max-w-3xl p-3" id="chat-form">
    <InputGroup>
      <InputGroupTextarea id="chat-input" aria-label={t('chat.message')} placeholder={placeholder ?? t('chat.placeholder')} disabled={disabled}
        className="max-h-40 min-h-14" value={text} onChange={e => setText(e.target.value)}
        onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey && !e.nativeEvent.isComposing) { e.preventDefault(); form.current?.requestSubmit() } }} />
      <InputGroupAddon align="block-end" className="pt-1">
        {text.length > MAX_MESSAGE * 0.9 && <InputGroupText id="chat-count" className={text.length > MAX_MESSAGE ? 'text-destructive' : undefined}>{text.length}/{MAX_MESSAGE}</InputGroupText>}
        {running
          ? <InputGroupButton type="button" size="icon-sm" variant="outline" className="ml-auto rounded-full" id="chat-stop" aria-label={t('chat.stop')} onClick={onStop}><Square /></InputGroupButton>
          : <InputGroupButton type="submit" size="icon-sm" variant="default" className="ml-auto rounded-full" id="chat-send" aria-label={t('chat.send')} disabled={!canSend}><ArrowUp /></InputGroupButton>}
      </InputGroupAddon>
    </InputGroup>
  </form>
}
