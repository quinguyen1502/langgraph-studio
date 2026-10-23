/** A Human node in a chat (TASK-0085, DEC-0054), after the AI Elements Confirmation pattern: the person chatting
 *  answers it right here (approve, reject or a reply); a reviewer step only says it waits for the Approvals inbox. */
import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'
import { Hourglass, UserCheck } from 'lucide-react'
import { Bubble, BubbleContent } from '@/components/ui/bubble'
import { Marker, MarkerContent, MarkerIcon } from '@/components/ui/marker'
import { HumanAnswer } from '@/components/human-answer'
import type { ChatTurn } from '@/lib/chat'

export function ChatConfirmation({ turn, busy, onAnswer }: { turn: ChatTurn; busy: boolean; onAnswer: (response: string) => void }) {
  const { t } = useTranslation()
  if (turn.answered_by === 'reviewer') return <Marker id="chat-waiting-reviewer" className="px-1">
    <MarkerIcon><Hourglass /></MarkerIcon>
    <MarkerContent>{t('chat.waitingReviewer')} <Link to="/approvals" className="text-foreground">{t('chat.openApprovals')}</Link></MarkerContent>
  </Marker>
  return <Bubble variant="outline" className="max-w-[min(32rem,90%)]" id="chat-confirmation">
    <BubbleContent className="space-y-2">
      <div className="flex items-center gap-2 text-xs font-medium text-node-human"><UserCheck className="size-4" />{t('chat.needsAnswer')}</div>
      <HumanAnswer busy={busy} onRespond={onAnswer} />
    </BubbleContent>
  </Bubble>
}
