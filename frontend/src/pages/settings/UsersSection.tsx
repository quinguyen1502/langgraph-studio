/** Settings → Users (TASK-0014, admins): every account with its role and status, and the roles matrix. */
import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { AlertCircle, Check, Loader2, Minus } from 'lucide-react'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Switch } from '@/components/ui/switch'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { api } from '@/lib/api'
import { fmtDate } from '@/lib/i18n'
import { can, useMe, type AdminUser, type RoleMatrix } from '@/lib/rbac'

type Data = RoleMatrix & { users: AdminUser[] }

export function UsersSection() {
  const { t } = useTranslation(); const me = useMe()
  const [data, setData] = useState<Data | null>(null); const [err, setErr] = useState(''); const [busy, setBusy] = useState<string | null>(null)
  const load = () => api<Data>('/api/admin/users').then(d => { setData(d); setErr('') }).catch(e => setErr(e.message))
  useEffect(() => { if (can(me, 'users.manage')) load() }, [me])
  const patch = async (u: AdminUser, json: Partial<AdminUser>) => {
    setBusy(u.id); setErr('')
    try { const n = await api<AdminUser>(`/api/admin/users/${u.id}`, { method: 'PATCH', json }); setData(d => d && { ...d, users: d.users.map(x => x.id === n.id ? { ...x, ...n } : x) }) }
    catch (e: any) { setErr(e.message) } finally { setBusy(null) }
  }
  if (me && !can(me, 'users.manage')) return <Alert id="users-forbidden"><AlertCircle /><AlertDescription>{t('users.adminOnly')}</AlertDescription></Alert>
  if (!data) return err ? <Alert variant="destructive"><AlertCircle /><AlertDescription>{err}</AlertDescription></Alert>
    : <div className="flex items-center gap-2 text-sm text-muted-foreground"><Loader2 className="size-4 animate-spin" />{t('common.loading')}</div>
  return <div className="space-y-4">
    {err && <Alert variant="destructive" id="users-error"><AlertCircle /><AlertDescription>{err}</AlertDescription></Alert>}
    <Card className="overflow-hidden p-0"><Table id="users-table">
      <TableHeader><TableRow><TableHead className="pl-4">{t('users.email')}</TableHead><TableHead>{t('users.role')}</TableHead><TableHead>{t('users.workflows')}</TableHead>
        <TableHead>{t('users.created')}</TableHead><TableHead className="pr-4">{t('users.active')}</TableHead></TableRow></TableHeader>
      <TableBody>{data.users.map(u => { const self = u.id === me?.id
        return <TableRow key={u.id} className="user-row" data-email={u.email}>
          <TableCell className="pl-4 font-medium"><div className="flex items-center gap-2">{u.email}{self && <Badge variant="secondary">{t('users.you')}</Badge>}</div></TableCell>
          <TableCell><Select value={u.role} disabled={self || busy === u.id} onValueChange={v => patch(u, { role: v as AdminUser['role'] })}>
            <SelectTrigger size="sm" className="w-32" aria-label={t('users.roleFor', { email: u.email })}><SelectValue /></SelectTrigger>
            <SelectContent>{data.roles.map(r => <SelectItem key={r.role} value={r.role}>{t(`users.roles.${r.role}`)}</SelectItem>)}</SelectContent></Select></TableCell>
          <TableCell><Badge variant="secondary">{u.workflows}</Badge></TableCell>
          <TableCell className="text-muted-foreground">{u.created ? fmtDate(u.created) : '—'}</TableCell>
          <TableCell className="pr-4"><div className="flex items-center gap-2"><Switch checked={u.active} disabled={self || busy === u.id} aria-label={t('users.activeFor', { email: u.email })} onCheckedChange={v => patch(u, { active: v })} />
            <span className={u.active ? 'text-sm' : 'text-sm text-muted-foreground'}>{t(u.active ? 'users.statusActive' : 'users.statusDisabled')}</span></div></TableCell>
        </TableRow> })}</TableBody></Table></Card>
    <Card id="roles-matrix"><CardHeader><CardTitle>{t('users.matrixTitle')}</CardTitle><CardDescription>{t('users.matrixIntro')}</CardDescription></CardHeader>
      <CardContent className="space-y-4">
        <Table><TableHeader><TableRow><TableHead>{t('users.permission')}</TableHead>{data.roles.map(r => <TableHead key={r.role} className="text-center">{t(`users.roles.${r.role}`)}</TableHead>)}</TableRow></TableHeader>
          <TableBody>{data.permissions.map(p => <TableRow key={p}><TableCell><div className="font-medium">{t(`users.perms.${p.replace('.', '_')}`)}</div><div className="font-mono text-xs text-muted-foreground">{p}</div></TableCell>
            {data.roles.map(r => <TableCell key={r.role} className="text-center">{r.permissions.includes(p) ? <Check className="inline size-4 text-primary" aria-label={t('users.yes')} /> : <Minus className="inline size-4 text-muted-foreground" aria-label={t('users.no')} />}</TableCell>)}</TableRow>)}</TableBody></Table>
        <div className="space-y-1"><div className="text-sm font-medium">{t('users.accessTitle')}</div>
          {data.workflow_access.map(a => <div key={a.access} className="flex flex-wrap items-center gap-1.5 text-sm"><span className="w-28 text-muted-foreground">{t(`share.access.${a.access}`)}</span>
            {a.actions.map(x => <Badge key={x} variant="outline">{t(`share.actions.${x}`)}</Badge>)}</div>)}
          <p className="text-xs text-muted-foreground">{t('users.accessNote')}</p></div>
      </CardContent></Card>
  </div>
}
