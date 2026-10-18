import { useEffect, useState } from 'react'

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
