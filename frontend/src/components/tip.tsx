/** A shadcn tooltip around one element, used instead of the browser's `title` tooltip. */
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip'

export function Tip({ tip, children }: { tip: React.ReactNode; children: React.ReactElement }) {
  if (!tip) return children
  return <Tooltip><TooltipTrigger asChild>{children}</TooltipTrigger><TooltipContent>{tip}</TooltipContent></Tooltip>
}
