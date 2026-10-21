import { useEffect, useState } from 'react'
import { api } from '@/lib/api'
import { INBOX_POLL_MS, type InboxItem } from '@/lib/approvals'

/** Polls the Approvals inbox count (every 30 s and on window focus). */
export function useInboxCount() {
  const [n, setN] = useState(0)
  useEffect(() => {
    let alive = true
    const load = () => api<InboxItem[]>('/api/approvals/inbox').then(xs => { if (alive) setN(xs.length) }).catch(() => {})
    load(); const id = setInterval(load, INBOX_POLL_MS)
    const onFocus = () => load(); window.addEventListener('focus', onFocus)
    return () => { alive = false; clearInterval(id); window.removeEventListener('focus', onFocus) }
  }, [])
  return n
}
