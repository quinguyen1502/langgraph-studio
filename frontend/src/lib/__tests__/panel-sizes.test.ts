import { beforeEach, describe, expect, it } from 'vitest'
import { PANEL_DEFAULT, PANEL_KEY, panelStore, parseSizes } from '../panel-sizes'

describe('parseSizes', () => {
  it('uses the defaults when nothing is stored or the value is corrupt', () => {
    expect(parseSizes(null)).toEqual(PANEL_DEFAULT)
    expect(parseSizes('{not json')).toEqual(PANEL_DEFAULT)
    expect(parseSizes('"wide"')).toEqual(PANEL_DEFAULT)
  })
  it('keeps stored sizes, rounds them, and clamps to the minimums', () => {
    expect(parseSizes(JSON.stringify({ left: 400.4, right: 100, bottom: 220 }))).toEqual({ left: 400, right: 260, bottom: 220 })
  })
  it('falls back per field for missing or non-numeric values', () => {
    expect(parseSizes(JSON.stringify({ left: 'x', bottom: Infinity }))).toEqual(PANEL_DEFAULT)
  })
})

describe('panelStore', () => {
  beforeEach(() => localStorage.clear())
  it('round-trips under one key', () => {
    panelStore.write({ left: 300, right: 420, bottom: 180 })
    expect(Object.keys(localStorage)).toEqual([PANEL_KEY])
    expect(panelStore.read()).toEqual({ left: 300, right: 420, bottom: 180 })
  })
  it('clearing site data restores the defaults', () => {
    panelStore.write({ left: 300, right: 420, bottom: 180 }); localStorage.clear()
    expect(panelStore.read()).toEqual(PANEL_DEFAULT)
  })
})
