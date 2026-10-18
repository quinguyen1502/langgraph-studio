import { StudioNode, Sticky } from './canvas-nodes'
import { TYPES } from './meta'

export const nodeTypes = { ...Object.fromEntries([...TYPES, 'code'].map(t => [t, StudioNode])), note: Sticky }
