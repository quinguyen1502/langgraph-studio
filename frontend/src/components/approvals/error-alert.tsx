import type { ReactNode } from 'react'
import { AlertCircle } from 'lucide-react'
import { Alert, AlertDescription } from '@/components/ui/alert'

export function ErrorAlert({ children }: { children: ReactNode }) {
  return <Alert variant="destructive"><AlertCircle /><AlertDescription>{children}</AlertDescription></Alert>
}
