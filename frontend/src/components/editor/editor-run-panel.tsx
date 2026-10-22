import { useState } from 'react'
import { ExternalLink, AlertTriangle, FlaskConical, ShieldAlert } from 'lucide-react'
import { JsonEditor } from '@/components/json-editor'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { HumanPanel } from '@/components/human-panel'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import i18n from '@/lib/i18n'
import { useTranslation } from 'react-i18next'
import { RunTrace } from '@/components/run-trace'
import { fmtCost, fmtMs } from '@/lib/trace'
import { Tip } from '@/components/tip'
import { ChannelLogo } from '@/components/approvals/channel-logo'
import { api } from '@/lib/api'
import { EditorTestsPanel, TestCaseDialog, type TestCase } from './editor-tests-panel'
import { EditorCodePanel } from './editor-code-panel'
import { useStudioCtx } from './studio-context'

/** Bottom panel: run input, logs, history, tests (TASK-0067) and the workflow as code (TASK-0071). */
export function EditorRunPanel() {
  const { t } = useTranslation()
  const { input, setInput, log, setLog, errors, history, tab, setTab, running, traceSel, setTraceSel, replay, setReplay, openRun, respond, trace, traceMeta, wid, source, edit } = useStudioCtx()
  // the "Test runs" switch lists the workflow's test runs instead of its other runs (TASK-0067)
  const [testRuns, setTestRuns] = useState<any[] | null>(null)
  const showTests = (on: boolean) => { if (!on || !wid) { setTestRuns(null); return } api<any[]>(`/api/workflows/${wid}/runs?tests=true`).then(setTestRuns).catch(() => setTestRuns([])) }
  const rows = testRuns ?? history
  // Save as test case (TASK-0068): a draft from the run opens in the test case editor; once saved, the Tests tab shows it
  const [draft, setDraft] = useState<TestCase | null>(null); const [picked, setPicked] = useState<string | null>(null); const [draftErr, setDraftErr] = useState('')
  const canSave = !!wid && edit && !source
  const saveCase = (rid: string) => api<Omit<TestCase, 'id' | 'last'>>(`/api/workflows/${wid}/tests/from-run/${rid}`, { method: 'POST' })
    .then(d => { setDraftErr(''); setDraft({ ...d, id: '', last: null }) }).catch(e => setDraftErr(e.message))
  const saveButton = (rid: string) => <Tip tip={t('tests.saveFromRun')}>
    <Button size="icon" variant="ghost" className="size-6" data-testid="save-test" aria-label={t('tests.saveFromRun')} onClick={() => saveCase(rid)}><FlaskConical className="size-3.5" /></Button></Tip>
  const finished = (s: string) => s !== 'running' && s !== 'queued' && s !== 'idle'
  return <section className="h-full min-h-0 flex flex-col">
      <Tabs value={tab} onValueChange={setTab} className="flex-1 min-h-0 flex flex-col gap-0">
        <div className="flex items-center gap-3 px-3 py-2 border-b">
          <TabsList><TabsTrigger value="input">{t('editor.tabInput')}</TabsTrigger><TabsTrigger value="logs">{t('editor.tabLogs')} {trace.spans.length > 0 && <Badge variant={trace.status === 'error' ? 'destructive' : 'secondary'} className="ml-1">{trace.spans.length}</Badge>}</TabsTrigger>
            <TabsTrigger value="history">{t('editor.tabHistory')}</TabsTrigger>{!source && <TabsTrigger value="tests" id="tests-tab">{t('tests.tab')}</TabsTrigger>}
            {!source && <TabsTrigger value="code" id="code-tab">{t('codeView.tab')}</TabsTrigger>}</TabsList>
          {errors.length > 0 && <Badge variant="destructive">{t('editor.errorsBadge', { count: errors.length })}</Badge>}
        </div>
        <TabsContent value="input" className="flex-1 min-h-0 p-3 flex gap-3">
          <JsonEditor id="run-input" value={input} onChange={setInput} className="h-full min-h-0 flex-1" />
          {errors.length > 0 && <ScrollArea className="w-1/2"><Alert variant="destructive" id="validation-errors"><AlertTriangle /><AlertTitle>{t('editor.errorsTitle', { count: errors.length })}</AlertTitle>
            <AlertDescription><ul className="list-disc pl-4 space-y-0.5 text-xs">{errors.map((e, i) => <li key={i} className="break-words">{e}</li>)}</ul></AlertDescription></Alert></ScrollArea>}
        </TabsContent>
        <TabsContent value="logs" className="flex-1 min-h-0">
          {trace.waiting?.runId && !running && <HumanPanel waiting={trace.waiting} onRespond={r => respond(trace.waiting!.runId!, r)} />}
          <RunTrace trace={trace} events={log as any} meta={traceMeta} selected={traceSel} onSelect={sp => setTraceSel(sp?.key ?? null)}
            replay={replay ?? undefined} onExitReplay={() => { setReplay(null); setLog([]); setTraceSel(null) }}
            actions={canSave && !running && trace.runId && finished(trace.status) ? <Button variant="ghost" size="sm" className="h-6 gap-1 px-2 text-xs" id="trace-save-test"
              onClick={() => saveCase(trace.runId!)}><FlaskConical className="size-3.5" />{t('tests.saveFromRun')}</Button> : undefined} />
        </TabsContent>
        <TabsContent value="history" className="flex-1 min-h-0">
          <ScrollArea className="h-full"><div className="p-3 space-y-1">
            {wid && !source && <div className="flex items-center gap-2 pb-1"><Switch id="history-tests" checked={testRuns !== null} onCheckedChange={showTests} />
              <Label htmlFor="history-tests" className="text-xs font-normal">{t('tests.showRuns')}</Label></div>}
            {!rows.length && <span className="text-muted-foreground text-xs">{t('editor.noRuns')}</span>}
            {draftErr && <Alert variant="destructive" className="py-2"><AlertDescription>{draftErr}</AlertDescription></Alert>}
            {rows.map(h => <div key={h.id} className="flex items-center gap-1">
              <button data-testid="history-row" onClick={() => openRun(h)}
              className="min-w-0 flex-1 flex items-center gap-3 rounded-md px-2 py-1.5 text-left text-xs hover:bg-accent">
              <span className="w-16 shrink-0"><Badge variant={h.status === 'ok' ? 'success' : h.status === 'timeout' ? 'warning' : h.status === 'cancelled' || h.status === 'expired' || h.status === 'paused' ? 'secondary' : h.status === 'waiting' ? 'outline' : 'destructive'}>{t(`status.${h.status}`)}</Badge></span>
              <span className="w-20 shrink-0 text-muted-foreground tabular-nums">{new Date(h.started * 1000).toLocaleTimeString(i18n.resolvedLanguage)}</span>
              <span className="w-20 shrink-0 font-mono text-muted-foreground">{h.id}</span>
              <span className="flex w-28 shrink-0 items-center gap-1">
              {h.source === 'api' && <Badge variant="outline" data-testid="history-source">API</Badge>}
              {h.source === 'schedule' && <Badge variant="outline" data-testid="history-source">{t('schedules.badge')}</Badge>}
              {h.source === 'chat' && <Tip tip={t('chatTriggers.from', { sender: h.chat?.sender ?? '?', trigger: h.chat?.trigger ?? '—' })}>
                <Badge variant="outline" data-testid="history-source">{h.chat?.kind && <ChannelLogo kind={h.chat.kind} className="size-3" />}{t('chatTriggers.badge')}</Badge></Tip>}
              {h.source === 'test' && <Badge variant="outline" data-testid="history-source">{t('tests.badge')}</Badge>}
              {h.code_runtime === 'subprocess' && <Tip tip={t('code.runUnisolated')}><Badge variant="warning" data-testid="history-unisolated"><ShieldAlert className="size-3" /></Badge></Tip>}
              <Tip tip={h.version ? t('versions.runVersion', { n: h.version }) : t('versions.runUnsaved')}>
                <Badge variant="secondary" data-testid="history-version">{h.version ? `v${h.version}` : t('versions.unsaved')}</Badge></Tip></span>
              <span className="min-w-0 truncate">{JSON.stringify(h.input)}</span>
              <span className="ml-auto flex shrink-0 items-center gap-2 text-muted-foreground tabular-nums">
                {h.metrics && <span className="w-20 text-right" data-testid="history-tokens">{t('trace.tokens', { count: h.metrics.tokens })}</span>}
                {h.metrics && <span className="w-12 text-right" data-testid="history-cost">{fmtCost(h.metrics.cost_usd)}</span>}
                <span className="flex w-16 justify-end">{h.metrics?.error_count > 0 && <Badge variant="destructive">{t('trace.errorCount', { count: h.metrics.error_count })}</Badge>}</span>
                <span className="w-14 text-right">{fmtMs(h.metrics?.duration_ms ?? (h.ended - h.started) * 1000)}</span>
                {h.trace_url && <ExternalLink className="size-3.5" aria-label={t('trace.openTrace')} />}{/* link itself is in the replayed timeline (no <a> inside a button) */}
              </span>
            </button>
            {canSave && <span className="flex w-6 shrink-0 justify-center">{finished(h.status) && saveButton(h.id)}</span>}</div>)}
          </div></ScrollArea>
        </TabsContent>
        <TabsContent value="tests" className="flex-1 min-h-0"><EditorTestsPanel select={picked} /></TabsContent>
        <TabsContent value="code" className="flex-1 min-h-0"><EditorCodePanel /></TabsContent>
      </Tabs>
      {draft && wid && <TestCaseDialog wid={wid} value={draft} onClose={() => setDraft(null)} onSaved={c => { setDraft(null); setPicked(c.id); setTab('tests') }} />}
    </section>
}
