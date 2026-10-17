import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'
import { Bell, CheckCheck } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuTrigger } from '@/components/ui/dropdown-menu'
import { api } from '@/lib/api'
import i18n from '@/lib/i18n'
import { cn } from '@/lib/utils'

type Note = { id: string; kind: 'run_waiting' | 'run_expired'; title: string; link: string | null; created: number; read: boolean
  params: { workflow_name?: string | null; label?: string | null; prompt?: string | null } }
const POLL_MS = 30_000

/** In-app notifications (TASK-0020): bell with unread count, list, mark read. */
export function NotificationBell() {
  const { t } = useTranslation(); const nav = useNavigate()
  const [items, setItems] = useState<Note[]>([]); const [unread, setUnread] = useState(0)
  const load = () => api<{ items: Note[]; unread: number }>('/api/notifications').then(d => { setItems(d.items); setUnread(d.unread) }).catch(() => {})
  useEffect(() => {
    load(); const id = setInterval(load, POLL_MS); window.addEventListener('focus', load)
    return () => { clearInterval(id); window.removeEventListener('focus', load) }
  }, [])
  const open = async (n: Note) => {
    if (!n.read) { try { const r = await api<{ unread: number }>(`/api/notifications/${n.id}/read`, { method: 'POST' }); setUnread(r.unread) } catch { /* ignore */ } }
    setItems(xs => xs.map(x => x.id === n.id ? { ...x, read: true } : x))
    if (n.link) nav(n.link)
  }
  const readAll = async () => { try { await api('/api/notifications/read-all', { method: 'POST' }); setUnread(0); setItems(xs => xs.map(x => ({ ...x, read: true }))) } catch { /* ignore */ } }
  const text = (n: Note) => t(`notify.${n.kind}`, { workflow: n.params.workflow_name || t('notify.unknownWorkflow'), label: n.params.label || '' })
  return <DropdownMenu onOpenChange={o => o && load()}>
    <DropdownMenuTrigger asChild><Button variant="ghost" size="icon" id="notify-bell" className="relative" aria-label={t('notify.unread', { count: unread })}>
      <Bell />{unread > 0 && <Badge className="absolute -top-1 -right-1 h-4 min-w-4 px-1 text-[10px]" data-testid="notify-count">{unread}</Badge>}</Button></DropdownMenuTrigger>
    <DropdownMenuContent align="end" className="w-80">
      <DropdownMenuLabel className="flex items-center justify-between">{t('notify.title')}
        {unread > 0 && <Button variant="ghost" size="sm" className="h-6" id="notify-read-all" onClick={e => { e.preventDefault(); readAll() }}><CheckCheck />{t('notify.markAll')}</Button>}</DropdownMenuLabel>
      <DropdownMenuSeparator />
      {!items.length && <div className="px-2 py-3 text-xs text-muted-foreground">{t('notify.empty')}</div>}
      {items.map(n => <DropdownMenuItem key={n.id} data-testid="notify-item" data-read={n.read} onClick={() => open(n)} className="flex items-start gap-2">
        <span className={cn('mt-1.5 size-2 shrink-0 rounded-full', n.read ? 'bg-transparent' : 'bg-primary')} />
        <span className="min-w-0 space-y-0.5"><span className={cn('block text-sm', !n.read && 'font-medium')}>{text(n)}</span>
          {n.params.prompt && <span className="block truncate text-xs text-muted-foreground">{n.params.prompt}</span>}
          <span className="block text-xs text-muted-foreground">{new Date(n.created * 1000).toLocaleString(i18n.resolvedLanguage)}</span></span>
      </DropdownMenuItem>)}
    </DropdownMenuContent>
  </DropdownMenu>
}
