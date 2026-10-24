import { useSyncExternalStore } from 'react'

const subscribe = (cb: () => void) => { addEventListener('resize', cb); return () => removeEventListener('resize', cb) }
/** The window's inner width, updated on resize. */
export const useViewportWidth = () => useSyncExternalStore(subscribe, () => window.innerWidth, () => 1440)
