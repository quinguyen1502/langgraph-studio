import { useMemo } from 'react'
import CodeMirror from '@uiw/react-codemirror'
import { python } from '@codemirror/lang-python'
import { HighlightStyle, syntaxHighlighting } from '@codemirror/language'
import { EditorView } from '@codemirror/view'
import { tags } from '@lezer/highlight'
import { cn } from '@/lib/utils'
import { editorTheme } from '@/lib/codemirror-theme'

const highlight = HighlightStyle.define([
  { tag: [tags.keyword, tags.controlKeyword, tags.definitionKeyword, tags.moduleKeyword, tags.operatorKeyword], color: 'var(--syntax-key)' },
  { tag: [tags.string, tags.special(tags.string)], color: 'var(--syntax-string)' },
  { tag: tags.number, color: 'var(--info)' },
  { tag: [tags.bool, tags.null, tags.self], color: 'var(--warning)' },
  { tag: tags.comment, color: 'var(--muted-foreground)', fontStyle: 'italic' },
  { tag: [tags.function(tags.definition(tags.variableName)), tags.definition(tags.className)], fontWeight: '600' },
])

/** Python source with highlighting (Tool node Code mode, TASK-0055); same look as the JSON editor. */
export function PythonEditor({ value, onChange, readOnly, id, className }: {
  value: string
  onChange?: (value: string) => void
  readOnly?: boolean
  id?: string
  className?: string
}) {
  const extensions = useMemo(() => [
    python(),
    syntaxHighlighting(highlight),
    editorTheme,
    EditorView.lineWrapping,  // a long line must not widen the config panel
    ...(id ? [EditorView.contentAttributes.of({ id, 'aria-label': 'Python' })] : []),
  ], [id])
  return <div className={cn('min-h-0 min-w-0 overflow-hidden rounded-lg border bg-muted/30', className)}>
    <CodeMirror value={value} height="100%" theme="none" editable={!readOnly} readOnly={!!readOnly}
      basicSetup={{ lineNumbers: true, foldGutter: false, highlightActiveLine: !readOnly, indentOnInput: true, tabSize: 4 }}
      extensions={extensions} onChange={onChange} className="h-full text-xs" />
  </div>
}
