import { Check, X } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { PASSWORD_RULES } from '@/lib/password'
import { cn } from '@/lib/utils'

/** The live checklist under a new-password field. */
export function PasswordRules({ id, password }: { id: string; password: string }) {
  const { t } = useTranslation()
  return <ul id={id} className="mt-1.5 space-y-0.5 text-xs">{PASSWORD_RULES.map(([k, f]) => { const ok = f(password); return <li key={k} className={cn('flex items-center gap-1.5', ok ? 'text-success' : 'text-muted-foreground')}>{ok ? <Check className="size-3" /> : <X className="size-3" />}{t(k)}</li> })}</ul>
}
