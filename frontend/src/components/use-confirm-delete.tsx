import { useState } from 'react'
import { ConfirmDeleteDialog, type ConfirmDeleteOptions } from '@/components/confirm-delete-dialog'

/** `const del = useConfirmDelete(); del.ask({...}); return <>{del.dialog}</>` — one dialog per screen, opened on demand. */
export function useConfirmDelete() {
  const [opts, setOpts] = useState<ConfirmDeleteOptions | null>(null)
  return {
    ask: (o: ConfirmDeleteOptions) => setOpts(o),
    close: () => setOpts(null),
    dialog: opts && <ConfirmDeleteDialog open onOpenChange={o => { if (!o) setOpts(null) }} {...opts} />,
  }
}
