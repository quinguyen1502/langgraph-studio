import { Languages, Check } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { Button } from '@/components/ui/button'
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu'
import { LANGS } from '@/lib/i18n'

export function LanguageSwitcher() {
  const { t, i18n } = useTranslation()
  return <DropdownMenu>
    <DropdownMenuTrigger asChild><Button variant="ghost" size="icon" id="lang-switch" aria-label={t('common.language')} title={t('common.language')}><Languages /></Button></DropdownMenuTrigger>
    <DropdownMenuContent align="end">
      {LANGS.map(l => <DropdownMenuItem key={l} data-lang={l} onClick={() => i18n.changeLanguage(l)}>
        <Check className={i18n.resolvedLanguage === l ? '' : 'invisible'} />{t(`lang.${l}`)}</DropdownMenuItem>)}
    </DropdownMenuContent>
  </DropdownMenu>
}
