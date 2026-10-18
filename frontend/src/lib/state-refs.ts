/** `{{state.field}}` references in node templates (TASK-0041). The pattern matches backend `engine/templating.py` VAR_RE. */
const VAR = String.raw`\{\{\s*state\.([A-Za-z_][A-Za-z0-9_]*)\s*\}\}`

/** A fresh global regex: group 1 is the field name. */
export const stateRefRe = () => new RegExp(VAR, 'g')

export const stateRef = (field: string) => `{{state.${field}}}`

/** A reference being typed at the end of `before`: where its `{{` starts and where the field name starts. */
export function openRef(before: string): { start: number; name: number } | null {
  const m = /\{\{\s*(?:state\.)?([A-Za-z0-9_]*)$/.exec(before)
  return m ? { start: m.index, name: before.length - m[1].length } : null
}

/** How many characters of `after` close a reference being completed (`}}`, with spaces before it). */
export function closeLen(after: string): number {
  return /^\s*\}\}/.exec(after)?.[0].length ?? 0
}
