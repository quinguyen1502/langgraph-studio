import { describe, expect, it } from 'vitest'
import { freeSpot, getCommands, grouped, registerCommands, searchValue, type PaletteCommand } from '../palette'

const C = (id: string, group: PaletteCommand['group'], extra: Partial<PaletteCommand> = {}): PaletteCommand => ({ id, group, label: id, run: () => {}, ...extra })

describe('command store', () => {
  it('registers, replaces and unregisters per source', () => {
    const off1 = registerCommands('editor', [C('save', 'actions')])
    const off2 = registerCommands('app', [C('nav:settings', 'navigation')])
    expect(getCommands().map(c => c.id)).toEqual(['save', 'nav:settings'])
    const off1b = registerCommands('editor', [C('run', 'actions')])
    off1()  // stale unregister must not remove the newer list
    expect(getCommands().map(c => c.id)).toEqual(['run', 'nav:settings'])
    off1b(); off2(); expect(getCommands()).toEqual([])
  })
})

describe('grouped', () => {
  it('orders groups, drops empty ones and duplicates', () => {
    const g = grouped([C('nav', 'navigation'), C('a', 'actions'), C('a', 'actions'), C('n1', 'nodes')])
    expect(g.map(([k, v]) => [k, v.map(c => c.id)])).toEqual([['actions', ['a']], ['nodes', ['n1']], ['navigation', ['nav']]])
  })
})

describe('helpers', () => {
  it('search value includes hint and keywords', () => {
    expect(searchValue(C('add:retriever', 'add', { label: 'Retriever', hint: 'Search a KB', keywords: ['rag'] }))).toBe('Retriever Search a KB rag add:retriever')
  })
  it('freeSpot centres the node and avoids existing ones', () => {
    expect(freeSpot({ x: 500, y: 300 }, [])).toEqual({ x: 400, y: 265 })
    expect(freeSpot({ x: 500, y: 300 }, [{ x: 400, y: 265 }, { x: 440, y: 305 }])).toEqual({ x: 520, y: 385 })
  })
})

describe('menuSections / openPalette', () => {
  it('lists only menu commands, in section order', async () => {
    const { menuSections } = await import('../palette')
    const s = menuSections([C('del', 'actions', { menu: 'danger' }), C('x', 'actions'), C('share', 'actions', { menu: 'workflow' }), C('tidy', 'actions', { menu: 'arrange' })])
    expect(s.map(([k, v]) => [k, v.map(c => c.id)])).toEqual([['arrange', ['tidy']], ['workflow', ['share']], ['danger', ['del']]])
  })
  it('notifies palette openers until unsubscribed', async () => {
    const { onPaletteRequest, openPalette } = await import('../palette')
    let n = 0; const off = onPaletteRequest(() => n++); openPalette(); off(); openPalette(); expect(n).toBe(1)
  })
})
