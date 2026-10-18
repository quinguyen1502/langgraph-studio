import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Check, Send, UserCheck, X } from 'lucide-react'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import type { Trace } from '@/lib/trace'

/** Shown above the run timeline while a run waits at a Human node (TASK-0006). */
export function HumanPanel({ waiting, onRespond }: { waiting: NonNullable<Trace['waiting']>; onRespond: (response: string) => void }) {
  const { t } = useTranslation(); const [text, setText] = useState('')
  return <Alert id="human-panel" className="m-3 w-auto border-node-human/40 bg-node-human-muted">
    <UserCheck className="text-node-human" />
    <AlertTitle>{t('human.title')}</AlertTitle>
    <AlertDescription className="space-y-2">
      <div className="text-xs text-muted-foreground">{t('human.node', { label: waiting.label || waiting.node })}</div>
      {waiting.prompt && <p id="human-question" className="text-sm text-foreground whitespace-pre-wrap">{waiting.prompt}</p>}
      <Textarea id="human-response" aria-label={t('human.response')} rows={2} className="text-xs bg-background" placeholder={t('human.placeholder')} value={text} onChange={e => setText(e.target.value)} />
      <div className="flex flex-wrap gap-2">
        <Button size="sm" id="human-approve" onClick={() => onRespond('approved')}><Check />{t('human.approve')}</Button>
        <Button size="sm" variant="outline" id="human-reject" onClick={() => onRespond('rejected')}><X />{t('human.reject')}</Button>
        <Button size="sm" variant="secondary" id="human-submit" disabled={!text.trim()} onClick={() => onRespond(text.trim())}><Send />{t('human.submit')}</Button>
      </div>
    </AlertDescription>
  </Alert>
}
