/** Admin view of where Tool nodes in Code mode run (TASK-0056): runtime, image, limits, and the risk of `subprocess`. */
import { useTranslation } from 'react-i18next'
import { ShieldAlert } from 'lucide-react'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useCodeRuntime } from '@/lib/code-runtime'

export function CodeRuntimeCard() {
  const { t } = useTranslation(); const rt = useCodeRuntime()
  if (!rt) return null
  const variant = rt.code_runtime === 'subprocess' ? 'warning' : rt.code_runtime === 'docker' && rt.available ? 'success' : 'secondary'
  const row = (label: string, value: React.ReactNode, id?: string) => <div className="flex flex-wrap items-center gap-2 text-sm"><span className="w-32 text-muted-foreground">{label}</span><span id={id}>{value}</span></div>
  return <Card id="code-runtime-card"><CardHeader><CardTitle>{t('code.adminTitle')}</CardTitle><CardDescription>{t('code.adminIntro')}</CardDescription></CardHeader>
    <CardContent className="space-y-2">
      {row(t('code.adminRuntime'), <Badge variant={variant} id="code-runtime-value">{t(`code.runtimes.${rt.code_runtime}`)}</Badge>)}
      {rt.code_runtime === 'docker' && row(t('code.adminImage'), <span className="font-mono text-xs">{rt.image}</span>)}
      {rt.code_runtime !== 'off' && row(t('code.adminLimits'), t('code.adminLimitsValue', { seconds: rt.limits.seconds, memory: rt.limits.memory, cpus: rt.limits.cpus, pids: rt.limits.pids }))}
      {rt.problem && <p className="text-xs text-muted-foreground" id="code-runtime-problem">{rt.problem}</p>}
      {rt.code_runtime === 'subprocess' && <Alert variant="warning" className="py-2" id="code-runtime-risk"><ShieldAlert /><AlertDescription className="text-xs">{t('code.adminRisk')}</AlertDescription></Alert>}
    </CardContent></Card>
}
