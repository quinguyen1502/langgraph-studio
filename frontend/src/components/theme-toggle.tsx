import { useTranslation } from 'react-i18next'
import { Moon, Sun } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useTheme } from '@/lib/theme'

export function ThemeToggle() {
  const { t } = useTranslation(); const { dark, setDark } = useTheme()
  return <Button variant="ghost" size="icon" id="theme-btn" title={t('common.darkMode')} aria-label={t('common.darkMode')} onClick={() => setDark(!dark)}>{dark ? <Sun /> : <Moon />}</Button>
}
