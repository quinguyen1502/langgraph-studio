import { describe, expect, it } from 'vitest'
import { fileName, previewLayout, readTemplateFile } from '../templates'

const n = (id: string, x: number, y: number) => ({ id, type: 'llm', position: { x, y } })

describe('previewLayout', () => {
  it('fits nodes inside the box with padding', () => {
    const p = previewLayout([n('a', 0, 0), n('b', 1000, 0), n('c', 500, 400)], 240, 96, 12)
    for (const v of Object.values(p)) { expect(v.x).toBeGreaterThanOrEqual(12); expect(v.x).toBeLessThanOrEqual(228); expect(v.y).toBeGreaterThanOrEqual(12); expect(v.y).toBeLessThanOrEqual(84) }
    expect(p.a.x).toBeLessThan(p.c.x); expect(p.c.x).toBeLessThan(p.b.x)
  })
  it('centres a single row and handles empty / single node', () => {
    const p = previewLayout([n('a', 0, 50), n('b', 100, 50)])
    expect(p.a.y).toBe(48)
    expect(previewLayout([])).toEqual({})
    expect(previewLayout([n('x', 5, 5)]).x).toEqual({ x: 120, y: 48 })
  })
})

describe('files', () => {
  it('slugs file names', () => {
    expect(fileName('My  Bot / v2')).toBe('my-bot-v2.template.json')
    expect(fileName('Ĩ')).toBe('template.template.json')
  })
  it('parses JSON or throws invalid-json', async () => {
    expect(await readTemplateFile(new File(['{"a":1}'], 'a.json'))).toEqual({ a: 1 })
    await expect(readTemplateFile(new File(['nope'], 'a.json'))).rejects.toThrow('invalid-json')
  })
})
