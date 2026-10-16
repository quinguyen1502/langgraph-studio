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
  const { dark, setDark } = useTheme()
  return <Button variant="ghost" size="icon" id="theme-btn" title="Dark mode" onClick={() => setDark(!dark)}>{dark ? <Sun /> : <Moon />}</Button>
}
