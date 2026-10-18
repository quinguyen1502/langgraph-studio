/** Input for `{{state.field}}` templates (TASK-0041): references show as tags, `{{` suggests state fields, the braces button inserts one. The value stays plain text. */
import { useMemo, useRef } from 'react'
import CodeMirror, { type ReactCodeMirrorRef } from '@uiw/react-codemirror'
import { autocompletion, type Completion, type CompletionContext } from '@codemirror/autocomplete'
import { EditorState } from '@codemirror/state'
import { Decoration, EditorView, MatchDecorator, ViewPlugin, WidgetType, placeholder as hint, type DecorationSet, type ViewUpdate } from '@codemirror/view'
import { Braces } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { Button } from '@/components/ui/button'
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel, DropdownMenuTrigger } from '@/components/ui/dropdown-menu'
import { closeLen, openRef, stateRef, stateRefRe } from '@/lib/state-refs'
import { cn } from '@/lib/utils'
import i18n from '@/lib/i18n'

export type TemplateField = { name: string; type?: string }

class Tag extends WidgetType {
  readonly name: string; readonly known: boolean
  constructor(name: string, known: boolean) { super(); this.name = name; this.known = known }
  eq(o: Tag) { return o.name === this.name && o.known === this.known }
  toDOM() {
    const s = document.createElement('span')
    s.className = cn('template-tag mx-px inline-block rounded-sm border px-1 align-baseline font-sans text-[11px] leading-4',
      this.known ? 'border-primary/30 bg-primary/10 text-primary' : 'border-destructive/40 bg-destructive/10 text-destructive')
    s.dataset.field = this.name; s.dataset.known = String(this.known)
    s.title = i18n.t(this.known ? 'template.tagTitle' : 'template.unknownTitle', { field: stateRef(this.name) })
    s.textContent = this.name
    return s
  }
}

/** Each reference becomes one atomic tag: the cursor steps over it and Backspace removes all of it. */
function tags(known: Set<string>) {
  const deco = new MatchDecorator({ regexp: stateRefRe(), decoration: m => Decoration.replace({ widget: new Tag(m[1], known.has(m[1])) }) })
  return ViewPlugin.fromClass(class {
    decorations: DecorationSet
    constructor(view: EditorView) { this.decorations = deco.createDeco(view) }
    update(u: ViewUpdate) { this.decorations = deco.updateDeco(u, this.decorations) }
  }, { decorations: p => p.decorations, provide: p => EditorView.atomicRanges.of(view => view.plugin(p)?.decorations ?? Decoration.none) })
}

/** After `{{`, list the state fields; picking one writes the whole reference, closing braces included. */
function suggest(fields: TemplateField[]) {
  return (ctx: CompletionContext) => {
    const line = ctx.state.doc.lineAt(ctx.pos)
    const open = openRef(line.text.slice(0, ctx.pos - line.from)); if (!open) return null
    const start = line.from + open.start
    const options: Completion[] = fields.map(f => ({ label: f.name, detail: f.type, type: 'variable',
      apply: (view, _c, _from, to) => {
        const end = to + closeLen(view.state.doc.sliceString(to, line.to)); const text = stateRef(f.name)
        view.dispatch({ changes: { from: start, to: end, insert: text }, selection: { anchor: start + text.length } })
      } }))
    return { from: line.from + open.name, options, validFor: /^[A-Za-z0-9_]*$/ }
  }
}

/** One-line fields: a pasted line break becomes a space (same length, so the selection stays valid). */
const oneLine = EditorState.transactionFilter.of(tr => {
  if (!tr.docChanged || tr.newDoc.lines === 1) return tr
  const changes: { from: number; to: number; insert: string }[] = []
  tr.changes.iterChanges((from, to, _f, _t, text) => changes.push({ from, to, insert: text.toString().replace(/[\r\n]/g, ' ') }))
  return { changes, selection: tr.selection, scrollIntoView: tr.scrollIntoView }
})

const theme = EditorView.theme({
  '&': { backgroundColor: 'transparent', color: 'var(--foreground)' },
  '&.cm-focused': { outline: 'none' },
  '.cm-scroller': { fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace', lineHeight: '1.5' },
  '.cm-content': { padding: '0' },
  '.cm-line': { padding: '0' },
  '.cm-placeholder': { color: 'var(--muted-foreground)' },
  '.cm-cursor, .cm-dropCursor': { borderLeftColor: 'var(--foreground)' },
  '.cm-selectionBackground, &.cm-focused .cm-selectionBackground, .cm-content ::selection': {
    backgroundColor: 'color-mix(in oklch, var(--primary) 25%, transparent)',
  },
  '.cm-tooltip': { backgroundColor: 'var(--popover)', color: 'var(--popover-foreground)', border: '1px solid var(--border)', borderRadius: 'var(--radius-md)', overflow: 'hidden' },
  '.cm-tooltip.cm-tooltip-autocomplete > ul': { fontFamily: 'inherit', maxHeight: '14em', minWidth: '10em' },
  '.cm-tooltip.cm-tooltip-autocomplete > ul > li': { padding: '2px 8px' },
  '.cm-tooltip.cm-tooltip-autocomplete > ul > li[aria-selected]': { backgroundColor: 'var(--accent)', color: 'var(--accent-foreground)' },
  '.cm-completionDetail': { color: 'var(--muted-foreground)', fontStyle: 'normal', marginLeft: '0.75em' },
  '.cm-completionMatchedText': { textDecoration: 'none', fontWeight: '600' },
})

const SETUP = { lineNumbers: false, foldGutter: false, highlightActiveLine: false, highlightActiveLineGutter: false, highlightSelectionMatches: false,
  closeBrackets: false, bracketMatching: false, autocompletion: false, searchKeymap: false, indentOnInput: false }

export function TemplateEditor({ value, onChange, fields, readOnly, singleLine, rows = 3, id, placeholder, className }: {
  value: string
  onChange: (value: string) => void
  fields: TemplateField[]
  readOnly?: boolean
  singleLine?: boolean
  /** Visible lines of a multi-line editor before it grows. */
  rows?: number
  /** Put on the editable element, as on an input. */
  id?: string
  placeholder?: string
  className?: string
}) {
  const { t } = useTranslation(); const cm = useRef<ReactCodeMirrorRef>(null)
  const key = JSON.stringify(fields.map(f => ({ name: f.name, type: f.type })))  // callers pass a new array on every render
  const extensions = useMemo(() => { const list: TemplateField[] = JSON.parse(key); return [
    tags(new Set(list.map(f => f.name))),
    autocompletion({ override: [suggest(list)], icons: false }),
    theme,
    EditorView.lineWrapping,
    ...(singleLine ? [oneLine] : []),
    ...(placeholder ? [hint(placeholder)] : []),
    EditorView.contentAttributes.of({ 'data-template': '', ...(id ? { id } : {}) }),
  ] }, [key, singleLine, placeholder, id])
  const insert = (name: string) => {
    const view = cm.current?.view; if (!view) return
    view.dispatch(view.state.replaceSelection(stateRef(name))); view.focus()  // focus moves now, not when the menu finishes closing
  }
  // The wrapper mirrors the shadcn Input/Textarea classes (including their dark: backgrounds) so it matches the inputs around it.
  return <div className={cn('relative min-w-0 rounded-lg border border-input bg-transparent py-1.5 pl-2.5 pr-8 text-xs transition-colors focus-within:border-ring focus-within:ring-3 focus-within:ring-ring/50 dark:bg-input/30',
    readOnly && 'cursor-not-allowed bg-input/50 opacity-50 dark:bg-input/80', className)}>
    <CodeMirror ref={cm} value={value} onChange={onChange} theme="none" editable={!readOnly} readOnly={!!readOnly} basicSetup={SETUP} extensions={extensions}
      minHeight={singleLine ? undefined : `${rows * 1.5}em`} maxHeight="20rem" />
    {/* not modal: a modal menu traps focus until it unmounts, so a key pressed right after picking would reach the canvas */}
    {!readOnly && <DropdownMenu modal={false}>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon-xs" className="absolute right-1 top-1 text-muted-foreground" aria-label={t('template.insert')} title={t('template.insert')}
          {...(id ? { id: `${id}-insert` } : {})}><Braces /></Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="max-h-72 min-w-40" onCloseAutoFocus={e => { e.preventDefault(); cm.current?.view?.focus() }}>
        <DropdownMenuLabel className="text-xs text-muted-foreground">{t('template.insert')}</DropdownMenuLabel>
        {fields.length ? fields.map(f => <DropdownMenuItem key={f.name} onSelect={() => insert(f.name)} className="font-mono text-xs">
          {f.name}{f.type && <span className="ml-auto pl-3 font-sans text-[11px] text-muted-foreground">{f.type}</span>}
        </DropdownMenuItem>) : <DropdownMenuItem disabled className="text-xs">{t('template.noFields')}</DropdownMenuItem>}
      </DropdownMenuContent>
    </DropdownMenu>}
  </div>
}
