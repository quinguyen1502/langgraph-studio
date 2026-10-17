import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'
import { UserCheck } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { api } from '@/lib/api'
import i18n from '@/lib/i18n'

type Pending = { id: string; workflow_id: string; workflow_name?: string; label?: string; prompt?: string; waiting_since?: number }

/** Runs of the current user paused at a Human node (TASK-0006). Hidden when there are none. */
export function PendingRuns() {
  const { t } = useTranslation(); const nav = useNavigate(); const [items, setItems] = useState<Pending[]>([])
  useEffect(() => { api<Pending[]>('/api/runs/pending').then(setItems).catch(() => {}) }, [])
  useEffect(() => { if (items.length && location.hash === '#pending-runs') document.getElementById('pending-runs')?.scrollIntoView() }, [items])
  if (!items.length) return null
  return <Card id="pending-runs" className="gap-2 py-4">
    <CardHeader className="px-4"><CardTitle className="flex items-center gap-2 text-base"><UserCheck className="size-4 text-node-human" />{t('human.pendingTitle')}<Badge variant="secondary">{items.length}</Badge></CardTitle>
      <CardDescription>{t('human.pendingDesc')}</CardDescription></CardHeader>
    <CardContent className="px-4 space-y-1">{items.map(p => <div key={p.id} data-testid="pending-row" className="flex items-center gap-3 rounded-md px-2 py-1.5 text-sm hover:bg-accent">
      <span className="font-medium truncate max-w-48">{p.workflow_name || p.workflow_id}</span>
      <span className="text-muted-foreground truncate max-w-40">{p.label}</span>
      <span className="truncate flex-1 text-muted-foreground">{p.prompt}</span>
      {p.waiting_since && <span className="text-xs text-muted-foreground tabular-nums">{new Date(p.waiting_since * 1000).toLocaleString(i18n.resolvedLanguage)}</span>}
      <Button size="sm" variant="outline" onClick={() => nav(`/workflows/${p.workflow_id}?run=${p.id}`)}>{t('human.respond')}</Button>
    </div>)}</CardContent>
  </Card>
}
