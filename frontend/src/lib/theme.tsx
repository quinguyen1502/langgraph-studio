import { useTranslation } from 'react-i18next'
import { useEffect, useState } from 'react'
import { Moon, Sun } from 'lucide-react'
import { Button } from '@/components/ui/button'

const initial = () => new URLSearchParams(location.search).get('theme') || localStorage.getItem('theme') || 'light'
let current = initial() === 'dark'
const subs = new Set<(d: boolean) => void>()
document.documentElement.classList.toggle('dark', current)
export function useTheme() {
  const [dark, setD] = useState(current)
  useEffect(() => { subs.add(setD); return () => { subs.delete(setD) } }, [])
  const setDark = (d: boolean) => { current = d; localStorage.setItem('theme', d ? 'dark' : 'light'); document.documentElement.classList.toggle('dark', d); subs.forEach(f => f(d)) }
  return { dark, setDark }
}
export function ThemeToggle() {
  const { t } = useTranslation(); const { dark, setDark } = useTheme()
  return <Button variant="ghost" size="icon" id="theme-btn" title={t('common.darkMode')} aria-label={t('common.darkMode')} onClick={() => setDark(!dark)}>{dark ? <Sun /> : <Moon />}</Button>
}
