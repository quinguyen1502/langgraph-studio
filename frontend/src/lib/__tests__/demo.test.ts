import { describe, expect, it } from 'vitest'
import { codeOffKey } from '@/lib/code-runtime'

describe('codeOffKey', () => {
  it('names the public demo when the server says so', () => {
    expect(codeOffKey({ demo: true } as any)).toBe('code.demoOff')
    expect(codeOffKey({ demo: false } as any)).toBe('code.off')
    expect(codeOffKey(null)).toBe('code.off')
  })
})
