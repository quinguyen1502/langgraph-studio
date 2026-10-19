import { describe, expect, it } from 'vitest'
import type { Edge, Node } from '@xyflow/react'
import { copySelection, parseClip, pasteClip, CLIP_FORMAT } from '../clipboard'

const N = (id: string, type: string, x = 0, y = 0, data: Record<string, unknown> = {}): Node => ({ id, type, position: { x, y }, data: { label: id, ...data } })
const nodes = [N('start', 'start'), N('a', 'llm', 100, 50, { credential_id: 'c1', _status: 'ok' }), N('b', 'tool', 300, 80), N('end', 'end', 500)]
const edges: Edge[] = [{ id: 'e1', source: 'start', target: 'a' }, { id: 'e2', source: 'a', target: 'b', label: 'yes' }, { id: 'e3', source: 'b', target: 'end' }]
let k = 0; const seed = () => `s${k++}`

describe('copySelection', () => {
  it('skips Start/End, keeps only internal edges and strips runtime fields', () => {
    const c = copySelection(nodes, edges, ['start', 'a', 'b', 'end'])!
    expect(c.format).toBe(CLIP_FORMAT); expect(c.nodes.map(n => n.id)).toEqual(['a', 'b'])
    expect(c.edges.map(e => e.id)).toEqual(['e2']); expect(c.edges[0].label).toBe('yes')
    expect(c.nodes[0].data._status).toBeUndefined(); expect(nodes[1].data._status).toBe('ok')
  })
  it('returns null when only protected nodes are selected', () => { expect(copySelection(nodes, edges, ['start', 'end'])).toBeNull() })
})

describe('pasteClip', () => {
  const clip = copySelection(nodes, edges, ['a', 'b'])!
  it('gives fresh unique ids, remaps edges, offsets and selects', () => {
    const r = pasteClip(clip, { existing: nodes.map(n => n.id), seed })
    expect(r.nodes).toHaveLength(2); expect(new Set(r.nodes.map(n => n.id)).size).toBe(2)
    for (const n of r.nodes) { expect(nodes.map(x => x.id)).not.toContain(n.id); expect(n.selected).toBe(true) }
    expect(r.nodes[0].position).toEqual({ x: 140, y: 90 })
    expect(r.edges).toHaveLength(1); expect(r.edges[0].source).toBe(r.nodes[0].id); expect(r.edges[0].target).toBe(r.nodes[1].id)
    expect(r.edges[0].label).toBe('yes')
  })
  it('pasting twice never collides; placing at a point moves the group top-left', () => {
    const one = pasteClip(clip, { existing: nodes.map(n => n.id), seed: () => 'x' })
    const two = pasteClip(clip, { existing: [...nodes, ...one.nodes].map(n => n.id), seed: () => 'x', at: { x: 1000, y: 500 } })
    expect(two.nodes.some(n => one.nodes.find(o => o.id === n.id))).toBe(false)
    expect(two.nodes[0].position).toEqual({ x: 1000, y: 500 }); expect(two.nodes[1].position).toEqual({ x: 1200, y: 530 })
  })
  it('clears credential refs the user cannot use and does not mutate the clip', () => {
    const r = pasteClip(clip, { existing: [], usableCredentials: new Set(['other']), seed })
    expect(r.nodes[0].data.credential_id).toBe(''); expect(r.clearedCredentials).toBe(1); expect(clip.nodes[0].data.credential_id).toBe('c1')
    expect(pasteClip(clip, { existing: [], usableCredentials: new Set(['c1']), seed }).nodes[0].data.credential_id).toBe('c1')
  })
})

describe('parseClip', () => {
  it('accepts only our versioned payload', () => {
    const c = copySelection(nodes, edges, ['a'])!
    expect(parseClip(JSON.stringify(c))?.nodes).toHaveLength(1)
    expect(parseClip('hello')).toBeNull(); expect(parseClip(JSON.stringify({ ...c, version: 2 }))).toBeNull(); expect(parseClip(null)).toBeNull()
  })
  it('still reads nodes copied under the v0.1.0 format name', () => {
    const c = copySelection(nodes, edges, ['a'])!
    expect(parseClip(JSON.stringify({ ...c, format: 'langgraph-studio/nodes' }))?.nodes).toHaveLength(1)
  })
})
