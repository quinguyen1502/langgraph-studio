/** Auto-layout (TASK-0027, DEC-0030): dagre layered layout using each node's measured size, left→right or top→bottom.
 * Pure; the editor applies the result in one state update, so it is one undo step. */
import dagre from '@dagrejs/dagre'
import type { Edge, Node } from '@xyflow/react'

export type Direction = 'LR' | 'TB'
export const DEFAULT_SIZE = { width: 200, height: 70 }
const size = (n: Node) => ({ width: n.measured?.width ?? n.width ?? DEFAULT_SIZE.width, height: n.measured?.height ?? n.height ?? DEFAULT_SIZE.height })

/** New positions for every node. `keepOrigin` anchors the result at the current top-left so the canvas doesn't jump. */
export function layoutGraph(nodes: Node[], edges: Edge[], dir: Direction = 'LR', keepOrigin = true): Node[] {
  if (!nodes.length) return nodes
  const g = new dagre.graphlib.Graph({ multigraph: true })
  g.setGraph({ rankdir: dir, nodesep: dir === 'LR' ? 50 : 70, ranksep: dir === 'LR' ? 100 : 80, marginx: 0, marginy: 0 })
  g.setDefaultEdgeLabel(() => ({}))
  const ids = new Set(nodes.map(n => n.id))
  nodes.forEach(n => g.setNode(n.id, size(n)))
  edges.forEach(e => { if (ids.has(e.source) && ids.has(e.target) && e.source !== e.target) g.setEdge(e.source, e.target, {}, e.id) })
  dagre.layout(g)
  const placed = nodes.map(n => { const p = g.node(n.id), s = size(n); return { ...n, position: { x: Math.round(p.x - s.width / 2), y: Math.round(p.y - s.height / 2) } } })
  if (!keepOrigin) return placed
  const ox = Math.min(...nodes.map(n => n.position.x)) - Math.min(...placed.map(n => n.position.x))
  const oy = Math.min(...nodes.map(n => n.position.y)) - Math.min(...placed.map(n => n.position.y))
  return placed.map(n => ({ ...n, position: { x: n.position.x + ox, y: n.position.y + oy } }))
}

/** Pairs of nodes whose boxes intersect (used by tests and as a safety check). */
export function overlaps(nodes: Node[]): [string, string][] {
  const out: [string, string][] = []
  for (let i = 0; i < nodes.length; i++) for (let j = i + 1; j < nodes.length; j++) {
    const a = nodes[i], b = nodes[j], sa = size(a), sb = size(b)
    if (a.position.x < b.position.x + sb.width && b.position.x < a.position.x + sa.width && a.position.y < b.position.y + sb.height && b.position.y < a.position.y + sa.height) out.push([a.id, b.id])
  }
  return out
}
