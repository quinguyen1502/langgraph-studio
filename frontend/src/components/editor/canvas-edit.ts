import { createContext } from 'react'

/** A sticky is canvas text, not a graph node. `editable` follows the workflow, not the canvas lock. */
export const CanvasEdit = createContext(false)
