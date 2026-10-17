import { useCallback, useRef, useState } from 'react'
import { changeKey, init, push, redo, snapshot, undo, type History, type Snap } from '@/lib/history'

/** Records graph snapshots as they change (skipping while a node is being dragged, so a drag is one step) and applies
 * undo/redo through `apply`. Call `reset` after loading or restoring a workflow. */
export function useGraphHistory(nodes: any[], edges: any[], state: any[], apply: (s: Snap) => void) {
  const h = useRef<History | null>(null); const [, bump] = useState(0)
  const dragging = nodes.some(n => n.dragging)
  if (h.current && !dragging) {
    const next = snapshot(nodes, edges, state)
    const after = push(h.current, next, changeKey(h.current.present, next))
    if (after !== h.current) h.current = after  // render-time bookkeeping only; no state update needed for content
  }
  const reset = useCallback((n: any[], e: any[], s: any[]) => { h.current = init(snapshot(n, e, s)); bump(x => x + 1) }, [])
  const go = (f: (x: History) => History) => {
    if (!h.current) return; const after = f(h.current); if (after === h.current) return
    h.current = after; apply(after.present); bump(x => x + 1)
  }
  return {
    undo: () => go(undo), redo: () => go(redo), reset,
    canUndo: !!h.current?.past.length, canRedo: !!h.current?.future.length,
  }
}
