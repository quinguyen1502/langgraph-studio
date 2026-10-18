/** Settings (/settings/:section): left navigation, one URL per section. New sections (credentials, API tokens)
 *  need an entry in SECTIONS (sections.ts) and in COMPONENTS. */
import type { ComponentType } from 'react'
import { useTranslation } from 'react-i18next'
import { Link, Navigate, useParams } from 'react-router-dom'
import { ArrowLeft, Workflow } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { LanguageSwitcher } from '@/components/language-switcher'
import { ThemeToggle } from '@/lib/theme'
import { UserMenu } from '@/components/user-menu'
import { cn } from '@/lib/utils'
import { ChannelsSection } from './ChannelsSection'
import { AccountsSection } from './AccountsSection'
import { AuditSection } from './AuditSection'
import { KnowledgeSection } from './KnowledgeSection'
import { McpSection } from './McpSection'
import { UsersSection } from './UsersSection'
import { TeamsSection } from './TeamsSection'
import { ActivitySection } from './ActivitySection'
import { can, useMe } from '@/lib/rbac'
import { SECTIONS, type SectionId } from './sections'

const COMPONENTS: Record<SectionId, ComponentType> = {
  channels: ChannelsSection, accounts: AccountsSection, audit: AuditSection, knowledge: KnowledgeSection,
  mcp: McpSection, users: UsersSection, teams: TeamsSection, activity: ActivitySection,
}

export function SettingsPage() {
  const { t } = useTranslation(); const { section } = useParams(); const me = useMe()
  const visible = SECTIONS.filter(s => !s.permission || can(me, s.permission))
  const current = SECTIONS.find(s => s.id === section)
  if (!current) return <Navigate to={`/settings/${SECTIONS[0].id}`} replace />
  const Component = COMPONENTS[current.id]
  return <div className="min-h-dvh bg-background">
    <header className="flex h-14 items-center gap-3 border-b px-6">
      <Link to="/workflows" className="flex items-center gap-2 font-semibold"><div className="rounded-md bg-primary p-1.5 text-primary-foreground"><Workflow className="size-4" /></div>LangGraph Studio</Link>
      <div className="ml-auto flex items-center gap-1"><LanguageSwitcher /><ThemeToggle /><UserMenu /></div>
    </header>
    <div className="mx-auto flex max-w-6xl flex-col gap-6 p-6 md:flex-row">
      <aside className="shrink-0 md:w-56">
        <Button variant="ghost" size="sm" asChild className="mb-3 -ml-2"><Link to="/workflows" id="settings-back"><ArrowLeft />{t('settings.back')}</Link></Button>
        <h1 className="mb-3 text-2xl font-semibold tracking-tight">{t('settings.title')}</h1>
        <nav className="flex gap-1 md:flex-col" aria-label={t('settings.title')}>
          {visible.map(s => <Button key={s.id} variant="ghost" asChild className={cn('justify-start', s.id === current.id && 'bg-accent text-accent-foreground')}>
            <Link to={`/settings/${s.id}`} id={`settings-nav-${s.id}`} aria-current={s.id === current.id ? 'page' : undefined}><s.icon />{t(`settings.nav.${s.id}`)}</Link>
          </Button>)}
        </nav>
      </aside>
      <main className="min-w-0 flex-1 space-y-4" id={`settings-${current.id}`}>
        <div><h2 className="text-xl font-semibold tracking-tight">{t(`settings.nav.${current.id}`)}</h2>
          <p className="text-sm text-muted-foreground">{t(`settings.intro.${current.id}`)}</p></div>
        <Component />
      </main>
    </div>
  </div>
}
