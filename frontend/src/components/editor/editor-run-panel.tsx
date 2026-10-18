import { ExternalLink, AlertTriangle } from 'lucide-react'
import { JsonEditor } from '@/components/json-editor'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { HumanPanel } from '@/components/human-panel'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import i18n from '@/lib/i18n'
import { useTranslation } from 'react-i18next'
import { RunTrace } from '@/components/run-trace'
import { fmtCost, fmtMs } from '@/lib/trace'
import { Tip } from './parts'
import { useStudioCtx } from './studio-context'

/** Bottom panel: run input, logs, and history (TASK-0040). */
export function EditorRunPanel() {
  const { t } = useTranslation()
  const { input, setInput, log, setLog, errors, history, tab, setTab, running, traceSel, setTraceSel, replay, setReplay, openRun, respond, trace, traceMeta } = useStudioCtx()
  return <section className="h-full min-h-0 flex flex-col">
      <Tabs value={tab} onValueChange={setTab} className="flex-1 min-h-0 flex flex-col gap-0">
        <div className="flex items-center gap-3 px-3 py-2 border-b">
          <TabsList><TabsTrigger value="input">{t('editor.tabInput')}</TabsTrigger><TabsTrigger value="logs">{t('editor.tabLogs')} {trace.spans.length > 0 && <Badge variant={trace.status === 'error' ? 'destructive' : 'secondary'} className="ml-1">{trace.spans.length}</Badge>}</TabsTrigger>
            <TabsTrigger value="history">{t('editor.tabHistory')}</TabsTrigger></TabsList>
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
            replay={replay ?? undefined} onExitReplay={() => { setReplay(null); setLog([]); setTraceSel(null) }} />
        </TabsContent>
        <TabsContent value="history" className="flex-1 min-h-0">
          <ScrollArea className="h-full"><div className="p-3 space-y-1">
            {!history.length && <span className="text-muted-foreground text-xs">{t('editor.noRuns')}</span>}
            {history.map(h => <button key={h.id} data-testid="history-row" onClick={() => openRun(h)}
              className="w-full flex items-center gap-3 rounded-md px-2 py-1.5 text-left text-xs hover:bg-accent">
              <Badge variant={h.status === 'ok' ? 'success' : h.status === 'timeout' ? 'warning' : h.status === 'cancelled' || h.status === 'expired' || h.status === 'paused' ? 'secondary' : h.status === 'waiting' ? 'outline' : 'destructive'}>{t(`status.${h.status}`)}</Badge>
              <span className="text-muted-foreground w-20">{new Date(h.started * 1000).toLocaleTimeString(i18n.resolvedLanguage)}</span>
              <span className="font-mono text-muted-foreground">{h.id}</span>
              {h.source === 'api' && <Badge variant="outline" data-testid="history-source">API</Badge>}
              <Tip tip={h.version ? t('versions.runVersion', { n: h.version }) : t('versions.runUnsaved')}>
                <Badge variant="secondary" data-testid="history-version">{h.version ? `v${h.version}` : t('versions.unsaved')}</Badge></Tip>
              <span className="truncate">{JSON.stringify(h.input)}</span>
              <span className="ml-auto flex shrink-0 items-center gap-2 text-muted-foreground tabular-nums">
                {h.metrics && <span data-testid="history-tokens">{t('trace.tokens', { count: h.metrics.tokens })}</span>}
                {h.metrics && <span data-testid="history-cost">{fmtCost(h.metrics.cost_usd)}</span>}
                {h.metrics?.error_count > 0 && <Badge variant="destructive">{t('trace.errorCount', { count: h.metrics.error_count })}</Badge>}
                <span>{fmtMs(h.metrics?.duration_ms ?? (h.ended - h.started) * 1000)}</span>
                {h.trace_url && <ExternalLink className="size-3.5" aria-label={t('trace.openTrace')} />}{/* link itself is in the replayed timeline (no <a> inside a button) */}
              </span>
            </button>)}
          </div></ScrollArea>
        </TabsContent>
      </Tabs>
    </section>
}
