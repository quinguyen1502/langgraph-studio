/** A run's node steps under an answer (TASK-0085, DEC-0053), with the shadcn Trace: labels show each node and its
 *  status; full also opens to the duration, input, output and errors. "none" renders nothing. */
import { useTranslation } from 'react-i18next'
import { CircleAlert, CircleCheck, Hourglass, Loader2 } from 'lucide-react'
import { Trace, TraceCollapsible, TraceCollapsibleContent, TraceCollapsibleTrigger, TraceDescription, TraceIcon, TraceLine, TraceTitle } from '@/components/ui/trace'
import { JsonView } from '@/components/json-view'
import { META } from '@/components/editor/meta'
import { fmtMs } from '@/lib/trace'
import type { ChatStep, StepsMode } from '@/lib/chat'

const STATUS = { ok: CircleCheck, error: CircleAlert, waiting: Hourglass, running: Loader2 } as const

function Line({ s }: { s: ChatStep }) {
  const { t } = useTranslation(); const I = STATUS[s.status]; const N = META[s.type ?? '']?.icon
  return <TraceLine status={s.status === 'error' ? 'error' : s.status === 'running' ? 'running' : undefined} data-testid="chat-step">
    <TraceIcon>{N ? <N /> : <I />}</TraceIcon><TraceTitle>{s.label}</TraceTitle>
    <TraceIcon><I className={s.status === 'running' ? 'animate-spin' : s.status === 'ok' ? 'text-success' : undefined} aria-label={t(`chat.step.${s.status}`)} /></TraceIcon>
    {s.duration_ms != null && <TraceDescription>{fmtMs(s.duration_ms)}</TraceDescription>}
  </TraceLine>
}

export function ChatSteps({ steps, mode }: { steps: ChatStep[]; mode: StepsMode }) {
  const { t } = useTranslation()
  if (mode === 'none' || !steps.length) return null
  return <Trace className="px-1" data-testid="chat-steps" data-mode={mode}>
    {steps.map((s, i) => mode === 'full'
      ? <TraceCollapsible key={`${s.node}-${i}`}>
          <TraceCollapsibleTrigger><Line s={s} /></TraceCollapsibleTrigger>
          <TraceCollapsibleContent><div className="space-y-2 py-1 pl-6 text-xs" data-testid="chat-step-detail">
            {s.errors?.length ? <p className="text-destructive">{s.errors.join('; ')}</p> : null}
            {s.input !== undefined && <div><div className="mb-1 text-muted-foreground">{t('chat.step.input')}</div><JsonView value={s.input} /></div>}
            {s.delta !== undefined && <div><div className="mb-1 text-muted-foreground">{t('chat.step.output')}</div><JsonView value={s.delta} /></div>}
          </div></TraceCollapsibleContent>
        </TraceCollapsible>
      : <div key={`${s.node}-${i}`}><Line s={s} /></div>)}
  </Trace>
}
