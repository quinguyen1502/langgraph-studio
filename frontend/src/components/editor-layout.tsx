import { useEffect, useRef, useState, type ReactNode } from 'react'
import { useTranslation } from 'react-i18next'
import { usePanelRef, type PanelSize } from 'react-resizable-panels'
import { ResizableHandle, ResizablePanel, ResizablePanelGroup } from '@/components/ui/resizable'
import { CANVAS_MIN, CHAT_WIDTH, PANEL_MIN, chatStore, panelStore, type PanelSizes } from '@/lib/panel-sizes'
import { cn } from '@/lib/utils'

/** Editor chrome (TASK-0038, REQ-0026): the 56px header, then palette | canvas | config over the run panel. The three
 * borders drag; the canvas takes what is left. Sizes are read once per mount and saved after a user drag only, so the
 * loading skeleton and the next workflow open with the same sizes.
 * Chat (TASK-0085) is a full-height column right of all of it, 340–760px, its width saved the same way. Config stays
 * beside the chat; `rightCollapsed` folds it away (narrow screens with nothing selected) and drags back open. */
export function EditorLayout({ header, left, canvas, right, bottom, chat, rightCollapsed = false, className, busy }: {
  header: ReactNode; left: ReactNode; canvas: ReactNode; right: ReactNode; bottom: ReactNode; chat?: ReactNode; rightCollapsed?: boolean; className?: string; busy?: boolean
}) {
  const { t } = useTranslation()
  const [init] = useState(panelStore.read)
  const [chatWidth] = useState(() => chatStore.read().width)
  const px = useRef<PanelSizes>({ ...init })
  const track = (k: keyof PanelSizes) => (s: PanelSize) => { if (s.inPixels > 0) px.current[k] = Math.round(s.inPixels) }
  const save = (_: unknown, meta: { isUserInteraction: boolean }) => { if (meta.isUserInteraction) panelStore.write(px.current) }
  const chatPx = useRef(chatWidth)
  const saveChat = (_: unknown, meta: { isUserInteraction: boolean }) => { if (meta.isUserInteraction) chatStore.write({ width: chatPx.current }) }
  const rightRef = usePanelRef()
  // after the chat column comes or goes the outer group lays out again, so apply the fold on the next frame
  const hasChat = !!chat
  useEffect(() => {
    const f = requestAnimationFrame(() => { const p = rightRef.current; if (!p) return
      if (rightCollapsed) { if (!p.isCollapsed()) p.collapse() } else if (p.isCollapsed()) p.expand() })
    return () => cancelAnimationFrame(f)
  }, [rightCollapsed, hasChat, rightRef])
  const side = { groupResizeBehavior: 'preserve-pixel-size', className: 'min-h-0' } as const
  return <div className={cn('h-screen flex flex-col bg-background', className)} aria-busy={busy || undefined}>
    {header}
    <ResizablePanelGroup orientation="horizontal" className="min-h-0 flex-1" onLayoutChanged={saveChat}>
      <ResizablePanel id="panel-editor" minSize={CANVAS_MIN.width + PANEL_MIN.left} className="min-h-0">
        <ResizablePanelGroup orientation="vertical" className="h-full min-h-0" onLayoutChanged={save}>
          <ResizablePanel id="panel-main" minSize={CANVAS_MIN.height} className="min-h-0">
            <ResizablePanelGroup orientation="horizontal" onLayoutChanged={save}>
              <ResizablePanel id="panel-left" defaultSize={init.left} minSize={PANEL_MIN.left} onResize={track('left')} {...side}>{left}</ResizablePanel>
              <ResizableHandle id="resize-left" aria-label={t('editor.resizePalette')} disableDoubleClick />
              <ResizablePanel id="panel-canvas" minSize={CANVAS_MIN.width} className="min-h-0">{canvas}</ResizablePanel>
              <ResizableHandle id="resize-right" aria-label={t('editor.resizeConfig')} disableDoubleClick />
              <ResizablePanel id="panel-right" panelRef={rightRef} defaultSize={rightCollapsed ? 0 : init.right} minSize={PANEL_MIN.right} collapsible collapsedSize={0}
                onResize={track('right')} {...side}>{right}</ResizablePanel>
            </ResizablePanelGroup>
          </ResizablePanel>
          <ResizableHandle id="resize-bottom" aria-label={t('editor.resizeRun')} disableDoubleClick />
          <ResizablePanel id="panel-bottom" defaultSize={init.bottom} minSize={PANEL_MIN.bottom} onResize={track('bottom')} {...side}>{bottom}</ResizablePanel>
        </ResizablePanelGroup>
      </ResizablePanel>
      {chat && <><ResizableHandle id="resize-chat" withHandle aria-label={t('chat.resize')} disableDoubleClick />
        <ResizablePanel id="panel-chat" defaultSize={chatWidth} minSize={CHAT_WIDTH.min} maxSize={CHAT_WIDTH.max}
          onResize={s => { if (s.inPixels > 0) chatPx.current = Math.round(s.inPixels) }} {...side}>{chat}</ResizablePanel></>}
    </ResizablePanelGroup>
  </div>
}
