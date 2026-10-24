import { beforeEach, describe, expect, it } from 'vitest'
import { CHAT_KEY, CHAT_WIDTH, PANEL_DEFAULT, PANEL_KEY, chatStore, panelStore, parseChat, parseSizes } from '../panel-sizes'

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

describe('chatStore', () => {
  beforeEach(() => localStorage.clear())
  it('defaults to closed at 420px and clamps the width to 340–760', () => {
    expect(chatStore.read()).toEqual({ open: false, width: CHAT_WIDTH.default })
    expect(parseChat(JSON.stringify({ open: true, width: 2000 }))).toEqual({ open: true, width: 760 })
    expect(parseChat(JSON.stringify({ open: 'yes', width: 100.6 }))).toEqual({ open: false, width: 340 })
    expect(parseChat('{bad')).toEqual({ open: false, width: 420 })
  })
  it('merges partial writes under one key', () => {
    chatStore.write({ open: true }); chatStore.write({ width: 500 })
    expect(Object.keys(localStorage)).toEqual([CHAT_KEY])
    expect(chatStore.read()).toEqual({ open: true, width: 500 })
  })
})
