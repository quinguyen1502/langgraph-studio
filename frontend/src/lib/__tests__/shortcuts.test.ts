import { describe, expect, it } from 'vitest'
import { keyCaps, matches, resolve, SHORTCUTS } from '../shortcuts'

const ev = (key: string, o: Partial<KeyboardEvent> = {}, target: any = null) =>
  ({ key, code: o.code ?? '', ctrlKey: false, metaKey: false, shiftKey: false, altKey: false, ...o, target }) as any

describe('matches', () => {
  it('maps mod to Ctrl off macOS and ⌘ on macOS', () => {
    expect(matches(ev('s', { ctrlKey: true }), 'mod+s', false)).toBe(true)
    expect(matches(ev('s', { metaKey: true }), 'mod+s', false)).toBe(false)
    expect(matches(ev('s', { metaKey: true }), 'mod+s', true)).toBe(true)
    expect(matches(ev('s', { ctrlKey: true }), 'mod+s', true)).toBe(false)
  })
  it('requires the exact modifiers', () => {
    expect(matches(ev('z', { ctrlKey: true, shiftKey: true }), 'mod+z', false)).toBe(false)
    expect(matches(ev('Z', { ctrlKey: true, shiftKey: true }), 'mod+shift+z', false)).toBe(true)
  })
  it('matches digits by code and punctuation by key', () => {
    expect(matches(ev('!', { shiftKey: true, code: 'Digit1' }), 'shift+1', false)).toBe(true)
    expect(matches(ev('?', { shiftKey: true }), '?', false)).toBe(true)
    expect(matches(ev('Enter', { ctrlKey: true }), 'mod+enter', false)).toBe(true)
  })
})

describe('resolve', () => {
  const input = Object.assign(document.createElement('input'), { type: 'text' })
  it('ignores canvas shortcuts while typing but keeps save/run', () => {
    expect(resolve(ev('Delete', {}, input), SHORTCUTS, false)).toBeUndefined()
    expect(resolve(ev('Delete', {}, document.body), SHORTCUTS, false)?.id).toBe('delete')
    expect(resolve(ev('s', { ctrlKey: true }, input), SHORTCUTS, false)?.id).toBe('save')
    expect(resolve(ev('?', { shiftKey: true }, input), SHORTCUTS, false)).toBeUndefined()
  })
  it('every shortcut id is unique', () => {
    expect(new Set(SHORTCUTS.map(s => s.id)).size).toBe(SHORTCUTS.length)
  })
})

describe('keyCaps', () => {
  it('renders per platform', () => {
    expect(keyCaps('mod+shift+z', false)).toEqual(['Ctrl', 'Shift', 'Z'])
    expect(keyCaps('mod+shift+z', true)).toEqual(['⌘', '⇧', 'Z'])
  })
})
