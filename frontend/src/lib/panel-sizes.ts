/** Editor panel sizes in px (TASK-0038, REQ-0026). One localStorage key in this browser; never part of the workflow,
 * so another author does not inherit them. Missing, corrupt or too-small values fall back to the defaults / minimums. */
export type PanelSizes = { left: number; right: number; bottom: number }

export const PANEL_KEY = 'lgs.editorPanels'
export const PANEL_DEFAULT: PanelSizes = { left: 250, right: 320, bottom: 300 }
export const PANEL_MIN: PanelSizes = { left: 180, right: 260, bottom: 140 }
export const CANVAS_MIN = { width: 280, height: 160 }

const KEYS = Object.keys(PANEL_DEFAULT) as (keyof PanelSizes)[]

export function parseSizes(raw: string | null): PanelSizes {
  let v: Record<string, unknown> | null = null
  try { v = JSON.parse(raw ?? 'null') } catch { /* corrupt value: defaults */ }
  const pick = (k: keyof PanelSizes) => { const n = v?.[k]; return typeof n === 'number' && Number.isFinite(n) ? Math.max(PANEL_MIN[k], Math.round(n)) : PANEL_DEFAULT[k] }
  return Object.fromEntries(KEYS.map(k => [k, pick(k)])) as PanelSizes
}

export const panelStore = {
  read: (): PanelSizes => { try { return parseSizes(localStorage.getItem(PANEL_KEY)) } catch { return { ...PANEL_DEFAULT } } },
  write: (s: PanelSizes) => { try { localStorage.setItem(PANEL_KEY, JSON.stringify(s)) } catch { /* storage disabled: sizes last for this page */ } },
}
