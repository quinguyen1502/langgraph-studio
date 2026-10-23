/** A chat's messages (TASK-0085) on the shadcn Message Scroller, Message and Bubble: the saved turns, then the
 *  message being sent and the live answer (its steps and the reply streaming in). */
import { useTranslation } from 'react-i18next'
import { Bot, Loader2 } from 'lucide-react'
import { MessageScroller, MessageScrollerButton, MessageScrollerContent, MessageScrollerItem, MessageScrollerProvider, MessageScrollerViewport } from '@/components/ui/message-scroller'
import { Message, MessageAvatar, MessageContent, MessageFooter } from '@/components/ui/message'
import { Bubble, BubbleContent } from '@/components/ui/bubble'
import { errorText } from '@/lib/i18n'
import { liveReply, liveSteps, waitingTurn, type ChatSettings, type ChatStep, type ChatTurn, type StepsMode } from '@/lib/chat'
import type { RunEvent, Trace } from '@/lib/trace'
import { ChatMarkdown } from './chat-markdown'
import { ChatSteps } from './chat-steps'
import { ChatConfirmation } from './chat-confirmation'

function Answer({ text, steps, mode, status, code, footer }: { text: string; steps?: ChatStep[]; mode: StepsMode; status?: string | null; code?: string | null; footer?: React.ReactNode }) {
  const { t } = useTranslation(); const failed = status && !['ok', 'waiting'].includes(status)
  return <Message data-testid="chat-answer" data-status={status ?? 'running'}>
    <MessageAvatar className="bg-muted text-muted-foreground"><Bot className="size-4" /></MessageAvatar>
    <MessageContent>
      <ChatSteps steps={steps ?? []} mode={mode} />
      {failed ? <Bubble variant="destructive"><BubbleContent data-testid="chat-error">{code ? errorText({ code, message: text }) : text || t('chat.failed')}</BubbleContent></Bubble>
        : text ? <Bubble variant="ghost"><BubbleContent><ChatMarkdown text={text} /></BubbleContent></Bubble> : null}
      {footer}
    </MessageContent>
  </Message>
}

const Mine = ({ text }: { text: string }) => <Message align="end" data-testid="chat-mine">
  <MessageContent><Bubble align="end" variant="secondary"><BubbleContent className="whitespace-pre-wrap">{text}</BubbleContent></Bubble></MessageContent></Message>

export function ChatThread({ turns, mode, settings, events, trace, pending, running, onAnswer }: {
  turns: ChatTurn[]; mode: StepsMode; settings: ChatSettings; events: RunEvent[]; trace: Trace; pending: string | null; running: boolean
  onAnswer: (runId: string, response: string) => void }) {
  const { t } = useTranslation(); const wait = waitingTurn(turns); const reply = liveReply(events, settings.reply_field)
  return <MessageScrollerProvider><MessageScroller className="flex-1">
    <MessageScrollerViewport><MessageScrollerContent className="mx-auto max-w-3xl gap-4 p-4" id="chat-thread">
      {!turns.length && !pending && <p className="m-auto text-center text-sm text-muted-foreground" id="chat-empty">{t('chat.empty')}</p>}
      {turns.map(x => <MessageScrollerItem key={x.id}>
        {x.role === 'user' ? <Mine text={x.text} />
          : <Answer text={x.text} steps={x.steps} mode={mode} status={x.status} code={x.code}
              footer={x === wait && !running ? <ChatConfirmation turn={x} busy={running} onAnswer={r => onAnswer(x.run_id!, r)} /> : undefined} />}
      </MessageScrollerItem>)}
      {pending !== null && <MessageScrollerItem scrollAnchor><Mine text={pending} /></MessageScrollerItem>}
      {pending !== null && <MessageScrollerItem>
        <Answer text={reply} steps={liveSteps(trace.spans, mode)} mode={mode}
          footer={<MessageFooter className="gap-1.5" id="chat-thinking"><Loader2 className="size-3 animate-spin" />{running ? t('chat.thinking') : t('chat.saving')}</MessageFooter>} />
      </MessageScrollerItem>}
    </MessageScrollerContent></MessageScrollerViewport>
    <MessageScrollerButton aria-label={t('chat.scrollEnd')} />
  </MessageScroller></MessageScrollerProvider>
}
