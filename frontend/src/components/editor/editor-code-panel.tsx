import { useEffect, useState } from 'react'
import { Check, Copy, Download } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { PythonEditor, type LineRange } from '@/components/python-editor'
import { api } from '@/lib/api'
import { useStudioCtx } from './studio-context'

type PythonExport = { filename: string; version: number | null; code: string; nodes: Record<string, LineRange[]> }

/** Code tab (TASK-0071, REQ-0043): the saved workflow as LangGraph code (Python for now; other languages can join
 * as more exporters); the node selected on the canvas shows where it is in the code. */
export function EditorCodePanel() {
  const { t } = useTranslation()
  const { wid, saves, selNode, isDirty } = useStudioCtx()
  const [out, setOut] = useState<PythonExport | null>(null); const [err, setErr] = useState(''); const [copied, setCopied] = useState(false)
  useEffect(() => {
    if (!wid) return
    let live = true
    api<PythonExport>(`/api/workflows/${wid}/python`).then(d => { if (live) { setOut(d); setErr('') } }).catch(e => { if (live) setErr(e.message) })
    return () => { live = false }
  }, [wid, saves])
  if (!wid) return <p className="p-3 text-xs text-muted-foreground" id="code-save-first">{t('codeView.saveFirst')}</p>
  const marks = selNode && out ? out.nodes[selNode.id] ?? [] : []
  const copy = () => { if (!out) return; void navigator.clipboard?.writeText(out.code); setCopied(true); setTimeout(() => setCopied(false), 1500) }
  const download = () => {
    if (!out) return
    const url = URL.createObjectURL(new Blob([out.code], { type: 'text/x-python' }))
    const a = document.createElement('a'); a.href = url; a.download = out.filename; a.click(); URL.revokeObjectURL(url)
  }
  return <div className="h-full min-h-0 flex flex-col gap-2 p-3">
    <div className="flex min-w-0 items-center gap-2 text-xs">
      <Badge variant="outline" id="code-language">{t('codeView.language')}</Badge>
      <span className="truncate font-mono" id="code-file">{out?.filename}</span>
      {out?.version != null && <Badge variant="secondary" id="code-version">{t('codeView.version', { n: out.version })}</Badge>}
      {isDirty() && <Badge variant="outline" className="border-warning text-warning" id="code-unsaved">{t('codeView.unsaved')}</Badge>}
      <span className="ml-auto truncate text-muted-foreground" id="code-hint">
        {selNode ? (marks.length ? t('codeView.showing', { node: (selNode.data as any)?.label || selNode.id }) : t('codeView.noCode')) : t('codeView.selectHint')}</span>
      <Button size="sm" variant="outline" className="h-7" id="code-copy" disabled={!out} onClick={copy}>{copied ? <Check /> : <Copy />}{t('common.copy')}</Button>
      <Button size="sm" variant="outline" className="h-7" id="code-download" disabled={!out} onClick={download}><Download />{t('codeView.download')}</Button>
    </div>
    {err && <Alert variant="destructive" className="py-2"><AlertDescription>{err}</AlertDescription></Alert>}
    <PythonEditor readOnly value={out?.code ?? ''} marks={marks} id="code-view" className="flex-1" />
  </div>
}
