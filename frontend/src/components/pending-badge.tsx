import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'
import { UserCheck } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip'
import { api } from '@/lib/api'

const POLL_MS = 30_000

/** Header badge: number of the user's runs waiting for a human response (TASK-0019). Hidden at 0. */
export function PendingBadge() {
  const { t } = useTranslation(); const nav = useNavigate(); const [n, setN] = useState(0)
  useEffect(() => {
    let alive = true
    const load = () => api<unknown[]>('/api/runs/pending').then(xs => { if (alive) setN(xs.length) }).catch(() => {})
    load(); const id = setInterval(load, POLL_MS)
    const onFocus = () => load(); window.addEventListener('focus', onFocus)
    return () => { alive = false; clearInterval(id); window.removeEventListener('focus', onFocus) }
  }, [])
  if (!n) return null
  return <Tooltip><TooltipTrigger asChild>
    <Button variant="ghost" size="sm" id="pending-badge" aria-label={t('human.pendingCount', { count: n })} onClick={() => nav('/workflows#pending-runs')}>
      <UserCheck className="text-node-human" /><Badge variant="secondary" data-testid="pending-count">{n}</Badge>
    </Button></TooltipTrigger><TooltipContent>{t('human.pendingCount', { count: n })}</TooltipContent></Tooltip>
}
