import { describe, expect, it } from 'vitest'
import { removeElements, selectionIds, spliceNode } from '../graph-ops'

const N = (id: string, type = 'llm', selected = false) => ({ id, type, position: { x: 0, y: 0 }, data: {}, selected }) as any
const E = (id: string, s: string, t: string, selected = false) => ({ id, source: s, target: t, selected }) as any
const nodes = [N('start', 'start'), N('a', 'llm', true), N('b'), N('end', 'end', true)]
const edges = [E('e1', 'start', 'a'), E('e2', 'a', 'b'), E('e3', 'b', 'end', true)]

describe('removeElements', () => {
  it('drops nodes with their edges but never Start/End', () => {
    const r = removeElements(nodes, edges, ['a', 'end'])
    expect(r.nodes.map(n => n.id)).toEqual(['start', 'b', 'end'])
    expect(r.edges.map(e => e.id)).toEqual(['e3'])
  })
  it('drops selected edges', () => {
    expect(removeElements(nodes, edges, [], ['e2']).edges.map(e => e.id)).toEqual(['e1', 'e3'])
  })
})

describe('selectionIds', () => {
  it('uses the canvas selection first, then the inspector item', () => {
    expect(selectionIds(nodes, edges)).toEqual({ nodeIds: ['a', 'end'], edgeIds: ['e3'] })
    const plain = nodes.map(n => ({ ...n, selected: false })); const pe = edges.map(e => ({ ...e, selected: false }))
    expect(selectionIds(plain, pe, { kind: 'edge', id: 'e1' })).toEqual({ nodeIds: [], edgeIds: ['e1'] })
  })
})

const at = (id: string, x: number, y = 0, selected = false) => ({ id, type: 'llm', position: { x, y }, data: {}, selected }) as any
const link = (id: string, source: string, target: string, extra: Record<string, unknown> = {}) => ({ id, source, target, ...extra }) as any

describe('spliceNode', () => {
  it('keeps the old edge label on the source-to-new half', () => {
    const before = [at('a', 0), at('b', 200, 0, true)]
    const old = [link('e1', 'a', 'b', { label: 'yes', conditional: true })]
    const r = spliceNode(before, old, at('n', 0), { dir: 'edge', edgeId: 'e1' })
    expect(r.nodes.map(n => n.id)).toEqual(['a', 'b', 'n'])
    expect(r.nodes.find(n => n.id === 'b')!.selected).toBe(false)
    expect(r.nodes.at(-1)!.position).toEqual({ x: 100, y: 0 })
    const first = r.edges.find(e => e.target === 'n')
    const second = r.edges.find(e => e.source === 'n')
    expect(first).toMatchObject({ source: 'a', target: 'n', label: 'yes', conditional: true })
    expect(first!.id).not.toBe('e1')
    expect(second).toMatchObject({ source: 'n', target: 'b' })
    expect((second as any).label).toBeUndefined()
    expect((second as any).conditional).toBeUndefined()
  })

  it('rewires the incoming edge when inserting before', () => {
    const r = spliceNode([at('a', 0), at('b', 200)], [link('e1', 'a', 'b', { label: 'go' })], at('n', 0), { dir: 'before', anchor: 'b' })
    expect(r.edges.find(e => e.id === 'e1')).toMatchObject({ source: 'a', target: 'n', label: 'go' })
    expect(r.edges.some(e => e.source === 'n' && e.target === 'b')).toBe(true)
  })

  it('rewires the outgoing edge when inserting after', () => {
    const r = spliceNode([at('a', 0), at('b', 200)], [link('e1', 'a', 'b', { label: 'go' })], at('n', 0), { dir: 'after', anchor: 'a' })
    expect(r.edges.find(e => e.id === 'e1')).toMatchObject({ source: 'n', target: 'b', label: 'go' })
    expect(r.edges.some(e => e.source === 'a' && e.target === 'n')).toBe(true)
  })

  it('adds only the bridge when the anchor has no neighbour', () => {
    const before = spliceNode([at('b', 100, 40)], [], at('n', 0), { dir: 'before', anchor: 'b' })
    expect(before.nodes.at(-1)!.position).toEqual({ x: -120, y: 40 })
    expect(before.edges).toMatchObject([{ source: 'n', target: 'b' }])
    const after = spliceNode([at('b', 100, 40)], [], at('n', 0), { dir: 'after', anchor: 'b' })
    expect(after.nodes.at(-1)!.position).toEqual({ x: 320, y: 40 })
    expect(after.edges).toMatchObject([{ source: 'b', target: 'n' }])
  })

  it('returns the same arrays when the edge or anchor is missing', () => {
    const graph = [at('a', 0)]
    const lines = [link('e1', 'a', 'gone')]
    const missingEdge = spliceNode(graph, lines, at('n', 0), { dir: 'edge', edgeId: 'nope' })
    expect(missingEdge.nodes).toBe(graph)
    expect(missingEdge.edges).toBe(lines)
    const missingAnchor = spliceNode(graph, lines, at('n', 0), { dir: 'before', anchor: 'nope' })
    expect(missingAnchor.nodes).toBe(graph)
    expect(missingAnchor.edges).toBe(lines)
  })
})
