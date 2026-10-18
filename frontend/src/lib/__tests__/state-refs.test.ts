import { describe, expect, it } from 'vitest'
import { closeLen, openRef, stateRef, stateRefRe } from '../state-refs'

describe('state refs', () => {
  it('finds references like the backend pattern, spaces allowed', () => {
    const names = (s: string) => [...s.matchAll(stateRefRe())].map(m => m[1])
    expect(names('Hi {{state.name}}, {{ state.order_id }}')).toEqual(['name', 'order_id'])
    expect(names('{{state.1x}} {{name}} {state.x}')).toEqual([])
  })
  it('builds a reference', () => expect(stateRef('message')).toBe('{{state.message}}'))
  it('spots a reference being typed', () => {
    expect(openRef('Hello {{')).toEqual({ start: 6, name: 8 })
    expect(openRef('Hello {{ state.mes')).toEqual({ start: 6, name: 15 })
    expect(openRef('Hello {{mes')).toEqual({ start: 6, name: 8 })
    expect(openRef('Hello {{state.message}} ')).toBeNull()
    expect(openRef('Hello {')).toBeNull()
  })
  it('measures closing braces after the cursor', () => {
    expect(closeLen('}} rest')).toBe(2)
    expect(closeLen(' }}')).toBe(3)
    expect(closeLen(' rest')).toBe(0)
  })
})
