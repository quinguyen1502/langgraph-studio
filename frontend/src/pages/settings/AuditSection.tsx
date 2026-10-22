/** Audit log of approval requests: filterable table (text, decision, platform). */
import { useEffect, useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Badge } from '@/components/ui/badge'
import { Card } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { ErrorAlert } from '@/components/approvals/channel-parts'
import { ChannelLogo } from '@/components/approvals/channel-logo'
import { FilterBar } from '@/components/settings/filter-bar'
import { api } from '@/lib/api'
import i18n, { errorText } from '@/lib/i18n'

type Audit = { id: string; at: number; kind: string; action: string; code: string | null; run_id: string | null; workflow_name: string | null; actor: string | null; external_id: string | null }
const ACTIONS = ['requested', 'approved', 'rejected', 'answered', 'reminded', 'escalated', 'escalation_skipped', 'timed_out', 'denied', 'superseded', 'expired', 'send_failed', 'not_configured', 'chat_started', 'chat_refused']
const VARIANT: Record<string, 'default' | 'secondary' | 'destructive' | 'outline'> = { approved: 'default', rejected: 'destructive', denied: 'outline', send_failed: 'destructive', chat_refused: 'outline' }

export function AuditSection() {
  const { t } = useTranslation(); const [items, setItems] = useState<Audit[] | null>(null); const [err, setErr] = useState('')
  const [q, setQ] = useState(''); const [action, setAction] = useState('all'); const [kind, setKind] = useState('all')
  useEffect(() => { api<Audit[]>('/api/approvals/audit').then(setItems).catch(e => setErr(e.message)) }, [])
  const kinds = useMemo(() => [...new Set((items || []).map(e => e.kind))].sort(), [items])
  const shown = useMemo(() => (items || []).filter(e => {
    const needle = q.trim().toLowerCase()
    return (!needle || [e.workflow_name, e.run_id, e.actor, e.external_id].some(v => v?.toLowerCase().includes(needle)))
      && (action === 'all' || e.action === action) && (kind === 'all' || e.kind === kind)
  }), [items, q, action, kind])
  return <div className="space-y-4">
    <FilterBar id="audit-filters" q={q} onQ={setQ} placeholder={t('settings.searchAudit')} filters={[
      { id: 'action', label: t('approvals.col.action'), value: action, onChange: setAction,
        options: [{ value: 'all', label: t('settings.filter.anyAction') }, ...ACTIONS.map(a => ({ value: a, label: t(`approvals.action.${a}`) }))] },
      { id: 'kind', label: t('approvals.platform'), value: kind, onChange: setKind,
        options: [{ value: 'all', label: t('settings.filter.anyPlatform') }, ...kinds.map(k => ({ value: k, label: t(`approvals.kind.${k}`), icon: <ChannelLogo kind={k} /> }))] },
    ]} />
    {err && <ErrorAlert>{err}</ErrorAlert>}
    {items && <p className="text-xs text-muted-foreground" id="audit-count">{t('settings.auditCount', { shown: shown.length, total: items.length })}</p>}
    {items && !items.length ? <p className="text-sm text-muted-foreground" id="audit-empty">{t('approvals.auditEmpty')}</p> : <Card className="py-0">
      <Table id="approval-audit">
        <TableHeader><TableRow><TableHead>{t('approvals.col.when')}</TableHead><TableHead>{t('approvals.col.action')}</TableHead><TableHead>{t('approvals.col.who')}</TableHead><TableHead>{t('approvals.col.run')}</TableHead></TableRow></TableHeader>
        <TableBody>{shown.map(e => <TableRow key={e.id} data-testid="audit-row">
          <TableCell className="whitespace-nowrap text-xs text-muted-foreground">{new Date(e.at * 1000).toLocaleString(i18n.resolvedLanguage)}</TableCell>
          <TableCell className="whitespace-normal"><div className="flex max-w-64 flex-col items-start gap-1"><Badge variant={VARIANT[e.action] || 'secondary'}>{t(`approvals.action.${e.action}`)}</Badge>
            {e.code && <span className="text-xs text-muted-foreground">{errorText({ code: e.code, details: { kind: t(`approvals.kind.${e.kind}`) } })}</span>}</div></TableCell>
          <TableCell className="whitespace-normal text-xs"><div className="max-w-48 truncate">{e.actor || '—'}</div><div className="flex items-center gap-1 text-muted-foreground"><ChannelLogo kind={e.kind} className="size-3.5" />{t(`approvals.kind.${e.kind}`)}{e.external_id && <span className="font-mono"> · {e.external_id}</span>}</div></TableCell>
          <TableCell className="text-xs"><div className="max-w-48 truncate">{e.workflow_name || '—'}</div><div className="font-mono text-muted-foreground">{e.run_id}</div></TableCell>
        </TableRow>)}
          {items && items.length > 0 && !shown.length && <TableRow><TableCell colSpan={4} className="py-8 text-center text-sm text-muted-foreground">{t('settings.noMatch')}</TableCell></TableRow>}
        </TableBody>
      </Table></Card>}
  </div>
}
