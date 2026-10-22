import { describe, expect, it } from 'vitest'
import { normCommand, sampleMessage, validCommand } from '../chat-triggers'

describe('chat triggers', () => {
  it('normalises command words like the server', () => {
    expect(normCommand(' /Leave ')).toBe('leave')
    expect(validCommand('leave-2')).toBe(true)
    expect(validCommand('two words')).toBe(false)
    expect(validCommand('x'.repeat(33))).toBe(false)
    expect(validCommand('')).toBe(false)
  })
  it('shows what to type in each place', () => {
    expect(sampleMessage('slack', 'C0HR', 'Leave', 'Superstep', '<text>')).toBe('@Superstep leave <text>')
    expect(sampleMessage('telegram', '-100123', 'leave', 'Superstep', '<text>')).toBe('/leave <text>')
    expect(sampleMessage('slack', 'dm', 'leave', 'Superstep', '<text>')).toBe('leave <text>')
    expect(sampleMessage('slack', 'C0HR', '', 'Superstep', '<text>')).toBe('@Superstep … <text>')
  })
})
