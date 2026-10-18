import { forwardRef } from 'react'
import { Link } from 'react-router-dom'
import { cn } from '@/lib/utils'

const linkClass = 'font-medium text-foreground underline underline-offset-2'

export function TextLink({ to, id, children, className }: { to: string; id?: string; children: React.ReactNode; className?: string }) {
  return <Link to={to} id={id} className={cn(linkClass, className)}>{children}</Link>
}

export const TextButton = forwardRef<HTMLButtonElement, React.ComponentProps<'button'>>(function TextButton({ className, type = 'button', ...props }, ref) {
  return <button ref={ref} type={type} className={cn(linkClass, className)} {...props} />
})
