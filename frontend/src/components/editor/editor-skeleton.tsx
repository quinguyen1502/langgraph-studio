import { Skeleton } from '@/components/ui/skeleton'
import { EditorLayout } from '@/components/editor-layout'
import { useTranslation } from 'react-i18next'

export function EditorSkeleton() {
  const { t } = useTranslation()
  return <EditorLayout busy
    header={<header className="h-14 shrink-0 flex items-center gap-3 border-b px-4"><span className="sr-only">{t('common.loading')}</span>
      <Skeleton className="size-8" /><Skeleton className="h-5 w-40" /><Skeleton className="h-8 w-72" /><Skeleton className="ml-auto h-8 w-28" />
    </header>}
    left={<aside className="h-full space-y-2 overflow-hidden p-3">{Array.from({ length: 6 }, (_, i) => <Skeleton key={i} className="h-12 w-full" />)}</aside>}
    canvas={<main className="h-full p-8"><Skeleton className="h-16 w-56 rounded-xl" /></main>}
    right={<aside className="h-full space-y-2 overflow-hidden p-3"><Skeleton className="h-4 w-24" /><Skeleton className="h-8 w-full" /><Skeleton className="h-24 w-full" /></aside>}
    bottom={<section className="h-full space-y-2 overflow-hidden p-3"><Skeleton className="h-8 w-48" /><Skeleton className="h-40 w-full" /></section>} />
}
