import { describe, expect, it } from 'vitest'
// @ts-expect-error plain ESM script without types
import { check } from '../../../scripts/check-ui-classes.mjs'

const run = (body: string) => check('/x/src/a.tsx', `import { Button } from '@/components/ui/button'\nimport { Skeleton } from '@/components/ui/skeleton'\nexport const A = () => <>${body}</>\n`)

describe('ui-class check', () => {
  it('flags height, vertical padding, leading-none and arbitrary text sizes on ui components', () => {
    const hits = run('<Button className="h-6 py-1 leading-none text-[10px] md:h-9">x</Button>')
    expect(hits[0].classes).toEqual(['h-6', 'py-1', 'leading-none', 'text-[10px]', 'md:h-9'])
  })
  it('ignores min-h/max-h, plain elements, dimension components and cn() inputs are scanned', () => {
    expect(run('<Button className="min-h-0 max-h-64 w-8">x</Button><div className="h-4" /><Skeleton className="h-4" />')).toEqual([])
    expect(run('<Button className={cn("gap-1", ok && "h-7")}>x</Button>')).toHaveLength(1)
  })
  it('flags size-* on a Button only', () => {
    expect(run('<Button size="icon" className="size-7">x</Button>')[0].classes).toEqual(['size-7'])
    expect(run('<Skeleton className="size-7" />')).toEqual([])
  })
  it('honours an inline opt-out with a reason', () => {
    expect(run('<Button /* ui-class-ok: 44px touch target */ className="h-11">x</Button>')).toEqual([])
    expect(run('<Button /* ui-class-ok: */ className="h-11">x</Button>')).toHaveLength(1)
  })
})
