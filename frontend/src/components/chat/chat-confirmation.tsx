/** A Human node in a chat (TASK-0085, DEC-0054), built as the shadcn Confirmation pattern: an outline Item with the
 *  question and Reject / Approve. A typed answer goes through the message box. A reviewer step is a Marker that
 *  points to the Approvals page instead. */
import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'
import { Hourglass, UserCheck } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Item, ItemActions, ItemContent, ItemDescription, ItemMedia, ItemTitle } from '@/components/ui/item'
import { Marker, MarkerContent, MarkerIcon } from '@/components/ui/marker'
import type { ChatTurn } from '@/lib/chat'

export function ChatConfirmation({ turn, busy, onAnswer }: { turn: ChatTurn; busy: boolean; onAnswer: (response: string) => void }) {
  const { t } = useTranslation()
  if (turn.answered_by === 'reviewer') return <Marker id="chat-waiting-reviewer">
    <MarkerIcon><Hourglass /></MarkerIcon>
    <MarkerContent>{t('chat.waitingReviewer')} <Link to="/approvals">{t('chat.openApprovals')}</Link></MarkerContent>
  </Marker>
  return <Item variant="outline" size="sm" id="chat-confirmation">
    <ItemMedia variant="icon"><UserCheck /></ItemMedia>
    <ItemContent><ItemTitle>{t('chat.needsAnswer')}</ItemTitle><ItemDescription>{t('chat.answerHint')}</ItemDescription></ItemContent>
    <ItemActions>
      <Button size="sm" variant="outline" id="chat-reject" disabled={busy} onClick={() => onAnswer('rejected')}>{t('human.reject')}</Button>
      <Button size="sm" id="chat-approve" disabled={busy} onClick={() => onAnswer('approved')}>{t('human.approve')}</Button>
    </ItemActions>
  </Item>
}
