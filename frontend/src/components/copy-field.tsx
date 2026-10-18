import { useState } from 'react'
import { Check, Copy } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

/** A read-only value with a copy button (callback URLs, password reset links). */
export function CopyField({ id, label, value }: { id: string; label: string; value: string }) {
  const { t } = useTranslation(); const [copied, setCopied] = useState(false)
  return <div className="space-y-1.5"><Label htmlFor={id}>{label}</Label>
    <div className="flex gap-2"><Input readOnly value={value} className="font-mono text-xs" id={id} />
      <Button variant="outline" size="icon" aria-label={t('common.copy')} onClick={() => { navigator.clipboard?.writeText(value); setCopied(true); setTimeout(() => setCopied(false), 1500) }}>{copied ? <Check /> : <Copy />}</Button></div></div>
}
