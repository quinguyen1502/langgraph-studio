import { useMemo } from 'react'
import CodeMirror from '@uiw/react-codemirror'
import { json } from '@codemirror/lang-json'
import { HighlightStyle, foldGutter, syntaxHighlighting } from '@codemirror/language'
import { EditorView } from '@codemirror/view'
import { editorTheme, foldIcon } from '@/lib/codemirror-theme'
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
    editorTheme,
    EditorView.lineWrapping,
    ...(id ? [EditorView.contentAttributes.of({ id })] : []),
  ], [id])
  return <div className={cn('min-h-0 min-w-0 overflow-hidden rounded-lg border bg-muted/30', className)}>
    <CodeMirror value={value} height="100%" theme="none" editable={!readOnly} readOnly={!!readOnly}
      basicSetup={{ lineNumbers: true, foldGutter: false, highlightActiveLine: !readOnly }}
      extensions={extensions} onChange={onChange} className="h-full text-xs" />
  </div>
}
