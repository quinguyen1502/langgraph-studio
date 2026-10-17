import { describe, expect, it } from 'vitest'
import type { Edge, Node } from '@xyflow/react'
import { layoutGraph, overlaps } from '../layout'

const N = (id: string, x = 0, y = 0, w?: number, h?: number): Node => ({ id, type: 'llm', position: { x, y }, data: {}, ...(w ? { measured: { width: w, height: h } } : {}) })
const E = (s: string, t: string): Edge => ({ id: `${s}-${t}`, source: s, target: t })
// a pile of nodes on top of each other with a branch
const nodes = [N('start'), N('a'), N('b', 0, 0, 320, 140), N('c'), N('end')]
const edges = [E('start', 'a'), E('a', 'b'), E('a', 'c'), E('b', 'end'), E('c', 'end')]

describe('layoutGraph', () => {
  it('removes overlaps and orders ranks left → right', () => {
    expect(overlaps(nodes).length).toBeGreaterThan(0)
    const r = layoutGraph(nodes, edges, 'LR'); const p = Object.fromEntries(r.map(n => [n.id, n.position]))
    expect(overlaps(r)).toEqual([])
    expect(p.start.x).toBeLessThan(p.a.x); expect(p.a.x).toBeLessThan(p.b.x); expect(p.b.x).toBeLessThan(p.end.x)
    expect(p.b.x).toBe(p.c.x + (200 - 320) / 2)  // same rank, centred despite the bigger measured size
  })
  it('orders ranks top → bottom with TB', () => {
    const r = layoutGraph(nodes, edges, 'TB'); const p = Object.fromEntries(r.map(n => [n.id, n.position]))
    expect(overlaps(r)).toEqual([]); expect(p.start.y).toBeLessThan(p.a.y); expect(p.a.y).toBeLessThan(p.end.y)
  })
  it('keeps the current top-left, ignores dangling edges and leaves input untouched', () => {
    const moved = nodes.map((n, i) => ({ ...n, position: { x: 500 + i, y: 300 + i } }))
    const r = layoutGraph(moved, [...edges, E('a', 'ghost'), E('c', 'c')], 'LR')
    expect(Math.min(...r.map(n => n.position.x))).toBe(500); expect(Math.min(...r.map(n => n.position.y))).toBe(300)
    expect(moved[0].position).toEqual({ x: 500, y: 300 }); expect(layoutGraph([], [])).toEqual([])
  })
})
