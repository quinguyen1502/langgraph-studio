import { useCallback, useState } from 'react'
import { changeKey, init, push, redo, snapshot, undo, type History, type Snap } from '@/lib/history'

/** Records graph snapshots as they change (skipping while a node is being dragged, so a drag is one step) and applies
 * undo/redo through `apply`. Call `reset` after loading or restoring a workflow. The history is state updated during
 * render when the graph changed (React's "adjust state when props change" pattern), so no extra effect pass. */
export function useGraphHistory(nodes: any[], edges: any[], state: any[], apply: (s: Snap) => void) {
  const [h, setH] = useState<History | null>(null)
  if (h && !nodes.some(n => n.dragging)) {
    const next = snapshot(nodes, edges, state)
    const after = push(h, next, changeKey(h.present, next))
    if (after !== h) setH(after)  // push returns the same history when nothing changed, so this settles in one pass
  }
  const reset = useCallback((n: any[], e: any[], s: any[]) => setH(init(snapshot(n, e, s))), [])
  const go = (f: (x: History) => History) => {
    if (!h) return; const after = f(h); if (after === h) return
    setH(after); apply(after.present)
  }
  return { undo: () => go(undo), redo: () => go(redo), reset, canUndo: !!h?.past.length, canRedo: !!h?.future.length }
}
