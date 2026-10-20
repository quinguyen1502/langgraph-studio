/** Search box + select filters, shared by the settings lists (channels, audit log). */
import { useTranslation } from 'react-i18next'
import { Search, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'

export type Filter = { id: string; label: string; value: string; onChange: (v: string) => void; options: { value: string; label: string }[] }

export function FilterBar({ id, q, onQ, placeholder, filters }: { id: string; q: string; onQ: (v: string) => void; placeholder: string; filters: Filter[] }) {
  const { t } = useTranslation()
  return <div className="flex flex-wrap items-center gap-2" id={id}>
    <div className="relative min-w-56 flex-1">
      <Search className="pointer-events-none absolute left-2.5 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
      <Input id={`${id}-search`} aria-label={placeholder} className="pl-8 pr-8" placeholder={placeholder} value={q}
        onChange={e => onQ(e.target.value)} onKeyDown={e => e.key === 'Escape' && onQ('')} />
      {q && <Button variant="ghost" size="icon" className="absolute right-0.5 top-0.5 size-7 text-muted-foreground" aria-label={t('settings.clear')} onClick={() => onQ('')}><X /></Button>}
    </div>
    {filters.map(f => <Select key={f.id} value={f.value} onValueChange={f.onChange}>
      <SelectTrigger className="w-44" id={`${id}-${f.id}`} aria-label={f.label}><SelectValue /></SelectTrigger>
      <SelectContent>{f.options.map(o => <SelectItem key={o.value} value={o.value}>{o.label}</SelectItem>)}</SelectContent>
    </Select>)}
  </div>
}
