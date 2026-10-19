import { useTranslation } from 'react-i18next'
import { Moon, Sun } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useTheme } from '@/lib/theme'
import { Tip } from '@/components/tip'

export function ThemeToggle() {
  const { t } = useTranslation(); const { dark, setDark } = useTheme()
  return <Tip tip={t('common.darkMode')}><Button variant="ghost" size="icon" id="theme-btn" aria-label={t('common.darkMode')} onClick={() => setDark(!dark)}>{dark ? <Sun /> : <Moon />}</Button></Tip>
}
