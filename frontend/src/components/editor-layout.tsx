import { useRef, useState, type ReactNode } from 'react'
import { useTranslation } from 'react-i18next'
import type { PanelSize } from 'react-resizable-panels'
import { ResizableHandle, ResizablePanel, ResizablePanelGroup } from '@/components/ui/resizable'
import { CANVAS_MIN, PANEL_MIN, panelStore, type PanelSizes } from '@/lib/panel-sizes'
import { cn } from '@/lib/utils'

/** Editor chrome (TASK-0038, REQ-0026): the 56px header, then palette | canvas | config over the run panel. The three
 * borders drag; the canvas takes what is left. Sizes are read once per mount and saved after a user drag only, so the
 * loading skeleton and the next workflow open with the same sizes. */
export function EditorLayout({ header, left, canvas, right, bottom, className, busy }: {
  header: ReactNode; left: ReactNode; canvas: ReactNode; right: ReactNode; bottom: ReactNode; className?: string; busy?: boolean
}) {
  const { t } = useTranslation()
  const [init] = useState(panelStore.read)
  const px = useRef<PanelSizes>({ ...init })
  const track = (k: keyof PanelSizes) => (s: PanelSize) => { px.current[k] = Math.round(s.inPixels) }
  const save = (_: unknown, meta: { isUserInteraction: boolean }) => { if (meta.isUserInteraction) panelStore.write(px.current) }
  const side = { groupResizeBehavior: 'preserve-pixel-size', className: 'min-h-0' } as const
  return <div className={cn('h-screen flex flex-col bg-background', className)} aria-busy={busy || undefined}>
    {header}
    <ResizablePanelGroup orientation="vertical" className="min-h-0 flex-1" onLayoutChanged={save}>
      <ResizablePanel id="panel-main" minSize={CANVAS_MIN.height} className="min-h-0">
        <ResizablePanelGroup orientation="horizontal" onLayoutChanged={save}>
          <ResizablePanel id="panel-left" defaultSize={init.left} minSize={PANEL_MIN.left} onResize={track('left')} {...side}>{left}</ResizablePanel>
          <ResizableHandle id="resize-left" aria-label={t('editor.resizePalette')} disableDoubleClick />
          <ResizablePanel id="panel-canvas" minSize={CANVAS_MIN.width} className="min-h-0">{canvas}</ResizablePanel>
          <ResizableHandle id="resize-right" aria-label={t('editor.resizeConfig')} disableDoubleClick />
          <ResizablePanel id="panel-right" defaultSize={init.right} minSize={PANEL_MIN.right} onResize={track('right')} {...side}>{right}</ResizablePanel>
        </ResizablePanelGroup>
      </ResizablePanel>
      <ResizableHandle id="resize-bottom" aria-label={t('editor.resizeRun')} disableDoubleClick />
      <ResizablePanel id="panel-bottom" defaultSize={init.bottom} minSize={PANEL_MIN.bottom} onResize={track('bottom')} {...side}>{bottom}</ResizablePanel>
    </ResizablePanelGroup>
  </div>
}
