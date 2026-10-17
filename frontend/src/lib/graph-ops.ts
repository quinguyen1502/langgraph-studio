/** Pure graph edits shared by keyboard shortcuts, buttons and (later) the history/clipboard (TASK-0023+). */
import type { Edge, Node } from '@xyflow/react'

/** Start and End anchor every workflow: they are never removed by a selection delete. */
export const PROTECTED = new Set(['start', 'end'])

/** Remove nodes (except protected ones) and edges by id, plus every edge touching a removed node. */
export function removeElements(nodes: Node[], edges: Edge[], nodeIds: Iterable<string>, edgeIds: Iterable<string> = []) {
  const gone = new Set([...nodeIds].filter(id => !PROTECTED.has(nodes.find(n => n.id === id)?.type ?? '')))
  const drop = new Set(edgeIds)
  return {
    nodes: nodes.filter(n => !gone.has(n.id)),
    edges: edges.filter(e => !drop.has(e.id) && !gone.has(e.source) && !gone.has(e.target)),
    removed: gone.size + edges.filter(e => drop.has(e.id)).length,
  }
}

/** What a Delete press removes: the React Flow selection, falling back to the inspector's selected item. */
export function selectionIds(nodes: Node[], edges: Edge[], fallback?: { kind: 'node' | 'edge'; id: string } | null) {
  const n = nodes.filter(x => x.selected).map(x => x.id); const e = edges.filter(x => x.selected).map(x => x.id)
  if (!n.length && !e.length && fallback) (fallback.kind === 'node' ? n : e).push(fallback.id)
  return { nodeIds: n, edgeIds: e }
}
