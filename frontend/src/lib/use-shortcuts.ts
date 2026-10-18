import { useEffect, useEffectEvent } from 'react'
import { resolve, SHORTCUTS, type Shortcut } from '@/lib/shortcuts'

/** Bind registry shortcuts (ignored while a modal dialog is open) to handlers while mounted. Handlers may return `false` to let the browser handle the key. */
export function useShortcuts(handlers: Partial<Record<string, (e: KeyboardEvent) => void | boolean>>, list: Shortcut[] = SHORTCUTS) {
  const handle = useEffectEvent((e: KeyboardEvent, id: string) => {  // always the latest handlers
    const h = handlers[id]; if (!h) return
    if (h(e) !== false) { e.preventDefault(); e.stopPropagation() }
  })
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.defaultPrevented || e.isComposing) return
      if (document.querySelector('[role=dialog][data-state=open], [role=alertdialog][data-state=open]')) return  // a modal owns the keyboard
      const s = resolve(e, list); if (s) handle(e, s.id)
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [list])
}
