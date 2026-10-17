import { describe, expect, it } from 'vitest'
import { COALESCE_MS, LIMIT, changeKey, init, push, redo, snapshot, undo } from '../history'

const node = (id: string, x = 0, data: any = { label: id }) => ({ id, type: 'llm', position: { x, y: 0 }, data })
const S = (nodes: any[], edges: any[] = [], state: any[] = []) => snapshot(nodes, edges, state)

describe('history', () => {
  it('undo and redo walk the stack; a new change clears redo', () => {
    let h = init(S([node('a')]))
    h = push(h, S([node('a'), node('b')]), null, 1)
    h = push(h, S([node('a'), node('b'), node('c')]), null, 2)
    h = undo(h); expect(h.present.nodes).toHaveLength(2)
    h = undo(h); expect(h.present.nodes).toHaveLength(1); expect(undo(h)).toBe(h)
    h = redo(h); expect(h.present.nodes).toHaveLength(2)
    h = push(h, S([node('z')]), null, 3); expect(h.future).toEqual([]); expect(redo(h)).toBe(h)
  })
  it('coalesces the same key inside the window only', () => {
    let h = init(S([node('a', 0, { label: 'a' })]))
    h = push(h, S([node('a', 0, { label: 'ab' })]), 'data:a', 100)
    h = push(h, S([node('a', 0, { label: 'abc' })]), 'data:a', 100 + COALESCE_MS - 1)
    expect(h.past).toHaveLength(1)
    h = push(h, S([node('a', 0, { label: 'abcd' })]), 'data:a', 100 + 3 * COALESCE_MS)
    expect(h.past).toHaveLength(2)
  })
  it('ignores no-op pushes and caps the past', () => {
    let h = init(S([node('a')])); expect(push(h, S([node('a')]))).toBe(h)
    for (let i = 1; i <= LIMIT + 20; i++) h = push(h, S([node('a', i)]), null, i)
    expect(h.past).toHaveLength(LIMIT)
  })
  it('snapshots drop runtime fields and selection', () => {
    const s = snapshot([{ ...node('a'), selected: true, data: { label: 'a', _status: 'done' } }], [{ id: 'e', source: 'a', target: 'b', selected: true, animated: true }], [])
    expect(s.nodes[0]).toEqual({ id: 'a', type: 'llm', position: { x: 0, y: 0 }, data: { label: 'a' } })
    expect(s.edges[0]).toEqual({ id: 'e', source: 'a', target: 'b' })
  })
})

describe('changeKey', () => {
  it('keys single-node setting edits and state edits; structure and moves get none', () => {
    const a = S([node('a'), node('b')])
    expect(changeKey(a, S([node('a', 0, { label: 'x' }), node('b')]))).toBe('data:a')
    expect(changeKey(a, S([node('a', 5), node('b')]))).toBeNull()
    expect(changeKey(a, S([node('a')]))).toBeNull()
    expect(changeKey(a, S([node('a'), node('b')], [], [{ name: 'f', type: 'string' }]))).toBe('state')
  })
})
