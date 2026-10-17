import { useState } from 'react'
/** Dialog open state that a parent may control (e.g. opened from the editor's ⋯ menu); uncontrolled otherwise. */
export function useOpenState(open?: boolean, onOpenChange?: (v: boolean) => void): [boolean, (v: boolean) => void, boolean] {
  const [inner, setInner] = useState(false)
  const controlled = open !== undefined
  return [controlled ? open : inner, (v: boolean) => { if (!controlled) setInner(v); onOpenChange?.(v) }, controlled]
}
