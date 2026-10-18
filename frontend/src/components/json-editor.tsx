import { useMemo } from 'react'
import CodeMirror from '@uiw/react-codemirror'
import { json } from '@codemirror/lang-json'
import { HighlightStyle, foldGutter, syntaxHighlighting } from '@codemirror/language'
import { EditorView } from '@codemirror/view'
import { tags } from '@lezer/highlight'
import { cn } from '@/lib/utils'

const highlight = HighlightStyle.define([
  { tag: tags.propertyName, color: 'var(--syntax-key)' },
  { tag: tags.string, color: 'var(--syntax-string)' },
  { tag: tags.number, color: 'var(--info)' },
  { tag: tags.bool, color: 'var(--warning)' },
  { tag: tags.null, color: 'var(--muted-foreground)' },
  { tag: [tags.punctuation, tags.separator], color: 'var(--muted-foreground)' },
])

/** Unicode fold marks sit on the em-box baseline, so the ink rides high. An icon centered in the line does not. */
function foldIcon(open: boolean) {
  const span = document.createElement('span')
  span.title = open ? 'Fold line' : 'Unfold line'
  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg')
  svg.setAttribute('viewBox', '0 0 24 24')
  svg.setAttribute('fill', 'none')
  svg.setAttribute('stroke', 'currentColor')
  svg.setAttribute('stroke-width', '2')
  svg.setAttribute('stroke-linecap', 'round')
  svg.setAttribute('stroke-linejoin', 'round')
  const path = document.createElementNS('http://www.w3.org/2000/svg', 'path')
  path.setAttribute('d', open ? 'm6 9 6 6 6-6' : 'm9 18 6-6-6-6')
  svg.append(path)
  span.append(svg)
  return span
}

const theme = EditorView.theme({
  '&': { height: '100%', backgroundColor: 'transparent', color: 'var(--foreground)' },
  '&.cm-focused': { outline: 'none' },
  '.cm-scroller': { overflow: 'auto', lineHeight: '1.5', fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace' },
  '.cm-content': { padding: '8px 0', minHeight: '100%' },
  '.cm-gutters': { backgroundColor: 'transparent', color: 'var(--muted-foreground)', borderRight: '1px solid var(--border)' },
  '.cm-activeLine, .cm-activeLineGutter': { backgroundColor: 'var(--accent)' },
  '.cm-selectionBackground, &.cm-focused .cm-selectionBackground, .cm-content ::selection': {
    backgroundColor: 'color-mix(in oklch, var(--primary) 25%, transparent)',
  },
  '.cm-cursor, .cm-dropCursor': { borderLeftColor: 'var(--foreground)' },
  '.cm-foldGutter .cm-gutterElement': { display: 'flex', alignItems: 'center', justifyContent: 'center' },
  '.cm-foldGutter svg': { width: '14px', height: '14px', display: 'block' },
})

export function JsonEditor({ value, onChange, readOnly, id, className }: {
  value: string
  onChange?: (value: string) => void
  readOnly?: boolean
  id?: string
  className?: string
}) {
  const extensions = useMemo(() => [
    json(),
    syntaxHighlighting(highlight),
    foldGutter({ markerDOM: foldIcon }),
    theme,
    EditorView.lineWrapping,
    ...(id ? [EditorView.contentAttributes.of({ id })] : []),
  ], [id])
  return <div className={cn('min-h-0 min-w-0 overflow-hidden rounded-lg border bg-muted/30', className)}>
    <CodeMirror value={value} height="100%" theme="none" editable={!readOnly} readOnly={!!readOnly}
      basicSetup={{ lineNumbers: true, foldGutter: false, highlightActiveLine: !readOnly }}
      extensions={extensions} onChange={onChange} className="h-full text-xs" />
  </div>
}
