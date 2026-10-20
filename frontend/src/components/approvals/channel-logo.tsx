/** Approval channel logos (TASK-0063). The one component file allowed to use brand colours (DEC-0042): marks are the
 *  platforms' own, unmodified, and only identify the integration. E-mail has no brand and uses a theme-coloured icon.
 *  Sources:
 *  - Slack: the 2019 mark, File:Slack_icon_2019.svg on Wikimedia Commons (a copy of the Slack Media Kit mark).
 *  - Microsoft Teams: the 2025 icon, File:Microsoft_Office_Teams_(2025–present).svg on Wikimedia Commons; gradient ids
 *    are prefixed per instance so two logos on one page never share them.
 *  - Telegram, WhatsApp: Simple Icons 16.35.0 (CC0 1.0), in the brand colours Simple Icons records (#26A5E4, #25D366).
 *    Telegram's plane is cut out of its circle, so a white disc behind it gives the official white-on-blue mark. */
import { useId, type ComponentProps, type ReactElement } from 'react'
import { useTranslation } from 'react-i18next'
import { Mail, MessageSquare } from 'lucide-react'
import { cn } from '@/lib/utils'

type Mark = (p: ComponentProps<'svg'>) => ReactElement

function TeamsMark(p: ComponentProps<'svg'>) {
  const id = `teams${useId().replace(/[^a-zA-Z0-9_-]/g, '')}`
  return <svg viewBox="4 4 36 38" fill="none" {...p}>
    <path fill={`url(#${id}a)`} d="M21.9999 20h12c3.3137 0 6 2.6863 6 6v10c0 3.3137-2.6863 6-6 6s-6-2.6863-6-6V26c0-3.3137-2.6863-6-6-6"/>
    <path fill={`url(#${id}b)`} d="M7.99988 24c0-3.3137 2.68632-6 6.00002-6h8c3.3137 0 6 2.6863 6 6v12c0 3.3137 2.6863 6 6 6l-16.0001-.0001c-5.5228 0-9.99992-4.4771-9.99992-10z"/>
    <path fill={`url(#${id}c)`} fillOpacity=".7" d="M7.99988 24c0-3.3137 2.68632-6 6.00002-6h8c3.3137 0 6 2.6863 6 6v12c0 3.3137 2.6863 6 6 6l-16.0001-.0001c-5.5228 0-9.99992-4.4771-9.99992-10z"/>
    <path fill={`url(#${id}d)`} fillOpacity=".7" d="M7.99988 24c0-3.3137 2.68632-6 6.00002-6h8c3.3137 0 6 2.6863 6 6v12c0 3.3137 2.6863 6 6 6l-16.0001-.0001c-5.5228 0-9.99992-4.4771-9.99992-10z"/>
    <path fill={`url(#${id}e)`} d="M32.9999 18c2.7614 0 5-2.2386 5-5s-2.2386-5-5-5-5 2.2386-5 5 2.2386 5 5 5"/>
    <path fill={`url(#${id}f)`} fillOpacity=".46" d="M32.9999 18c2.7614 0 5-2.2386 5-5s-2.2386-5-5-5-5 2.2386-5 5 2.2386 5 5 5"/>
    <path fill={`url(#${id}g)`} fillOpacity=".4" d="M32.9999 18c2.7614 0 5-2.2386 5-5s-2.2386-5-5-5-5 2.2386-5 5 2.2386 5 5 5"/>
    <path fill={`url(#${id}h)`} d="M17.9999 16c3.3137 0 6-2.6863 6-6 0-3.31371-2.6863-6-6-6s-6 2.68629-6 6c0 3.3137 2.6863 6 6 6"/>
    <path fill={`url(#${id}i)`} fillOpacity=".6" d="M17.9999 16c3.3137 0 6-2.6863 6-6 0-3.31371-2.6863-6-6-6s-6 2.68629-6 6c0 3.3137 2.6863 6 6 6"/>
    <path fill={`url(#${id}j)`} fillOpacity=".5" d="M17.9999 16c3.3137 0 6-2.6863 6-6 0-3.31371-2.6863-6-6-6s-6 2.68629-6 6c0 3.3137 2.6863 6 6 6"/>
    <rect width="16" height="16" x="4" y="23" fill={`url(#${id}k)`} rx="3.25"/>
    <rect width="16" height="16" x="4" y="23" fill={`url(#${id}l)`} fillOpacity=".7" rx="3.25"/>
    <path fill="#fff" d="M15.4792 28.1054h-2.4471v7.466h-2.0648v-7.466H8.52014v-1.6768h6.95906z"/>
    <defs>
    <radialGradient id={`${id}a`} cx="0" cy="0" r="1" gradientTransform="matrix(13.4784 0 0 33.2694 39.7967 22.1739)" gradientUnits="userSpaceOnUse">
    <stop stopColor="#a98aff"/>
    <stop offset=".14" stopColor="#8c75ff"/>
    <stop offset=".565" stopColor="#5f50e2"/>
    <stop offset=".9" stopColor="#3c2cb8"/>
    </radialGradient>
    <radialGradient id={`${id}b`} cx="0" cy="0" r="1" gradientTransform="rotate(68.1539 -7.71566095 14.71355834)scale(32.752 33.1231)" gradientUnits="userSpaceOnUse">
    <stop stopColor="#85c2ff"/>
    <stop offset=".69" stopColor="#7588ff"/>
    <stop offset="1" stopColor="#6459fe"/>
    </radialGradient>
    <radialGradient id={`${id}d`} cx="0" cy="0" r="1" gradientTransform="rotate(113.326 8.09285255 17.64474501)scale(19.2186 15.4273)" gradientUnits="userSpaceOnUse">
    <stop stopColor="#bd96ff"/>
    <stop offset=".686685" stopColor="#bd96ff" stopOpacity="0"/>
    </radialGradient>
    <radialGradient id={`${id}e`} cx="0" cy="0" r="1" gradientTransform="matrix(0 -10 12.6216 0 32.9999 11.5714)" gradientUnits="userSpaceOnUse">
    <stop offset=".268201" stopColor="#6868f7"/>
    <stop offset="1" stopColor="#3923b1"/>
    </radialGradient>
    <radialGradient id={`${id}f`} cx="0" cy="0" r="1" gradientTransform="rotate(40.0516 -.03068196 44.8729095)scale(7.14629 10.3363)" gradientUnits="userSpaceOnUse">
    <stop offset=".270711" stopColor="#a1d3ff"/>
    <stop offset=".813393" stopColor="#a1d3ff" stopOpacity="0"/>
    </radialGradient>
    <radialGradient id={`${id}g`} cx="0" cy="0" r="1" gradientTransform="rotate(-41.6581 32.11799918 -43.41948423)scale(8.51275 20.8824)" gradientUnits="userSpaceOnUse">
    <stop stopColor="#e3acfd"/>
    <stop offset=".816041" stopColor="#9fa2ff" stopOpacity="0"/>
    </radialGradient>
    <radialGradient id={`${id}h`} cx="0" cy="0" r="1" gradientTransform="matrix(0 -12 15.146 0 17.9999 8.28571)" gradientUnits="userSpaceOnUse">
    <stop offset=".268201" stopColor="#8282ff"/>
    <stop offset="1" stopColor="#3923b1"/>
    </radialGradient>
    <radialGradient id={`${id}i`} cx="0" cy="0" r="1" gradientTransform="rotate(40.0516 -3.15465147 21.41641466)scale(8.57554 12.4035)" gradientUnits="userSpaceOnUse">
    <stop offset=".270711" stopColor="#a1d3ff"/>
    <stop offset=".813393" stopColor="#a1d3ff" stopOpacity="0"/>
    </radialGradient>
    <radialGradient id={`${id}j`} cx="0" cy="0" r="1" gradientTransform="rotate(-41.6581 20.38180375 -26.51566158)scale(10.2153 25.0589)" gradientUnits="userSpaceOnUse">
    <stop stopColor="#e3acfd"/>
    <stop offset=".816041" stopColor="#9fa2ff" stopOpacity="0"/>
    </radialGradient>
    <radialGradient id={`${id}k`} cx="0" cy="0" r="1" gradientTransform="rotate(45 -25.76345597 16.32842712)scale(22.6274)" gradientUnits="userSpaceOnUse">
    <stop offset=".046875" stopColor="#688eff"/>
    <stop offset=".946875" stopColor="#230f94"/>
    </radialGradient>
    <radialGradient id={`${id}l`} cx="0" cy="0" r="1" gradientTransform="matrix(0 11.2 -13.0702 0 12 32.6)" gradientUnits="userSpaceOnUse">
    <stop offset=".570647" stopColor="#6965f6" stopOpacity="0"/>
    <stop offset="1" stopColor="#8f8fff"/>
    </radialGradient>
    <linearGradient id={`${id}c`} x1="20.5936" x2="20.5936" y1="18" y2="42" gradientUnits="userSpaceOnUse">
    <stop offset=".801159" stopColor="#6864f6" stopOpacity="0"/>
    <stop offset="1" stopColor="#5149de"/>
    </linearGradient>
    </defs>
  </svg>
}

const MARKS: Record<string, Mark> = {
  slack: p => <svg viewBox="0 0 127 127" {...p}>
    <path fill="#E01E5A" d="M27.2 80c0 7.3-5.9 13.2-13.2 13.2C6.7 93.2.8 87.3.8 80c0-7.3 5.9-13.2 13.2-13.2h13.2V80zm6.6 0c0-7.3 5.9-13.2 13.2-13.2 7.3 0 13.2 5.9 13.2 13.2v33c0 7.3-5.9 13.2-13.2 13.2-7.3 0-13.2-5.9-13.2-13.2V80z" />
    <path fill="#36C5F0" d="M47 27c-7.3 0-13.2-5.9-13.2-13.2C33.8 6.5 39.7.6 47 .6c7.3 0 13.2 5.9 13.2 13.2V27H47zm0 6.7c7.3 0 13.2 5.9 13.2 13.2 0 7.3-5.9 13.2-13.2 13.2H13.9C6.6 60.1.7 54.2.7 46.9c0-7.3 5.9-13.2 13.2-13.2H47z" />
    <path fill="#2EB67D" d="M99.9 46.9c0-7.3 5.9-13.2 13.2-13.2 7.3 0 13.2 5.9 13.2 13.2 0 7.3-5.9 13.2-13.2 13.2H99.9V46.9zm-6.6 0c0 7.3-5.9 13.2-13.2 13.2-7.3 0-13.2-5.9-13.2-13.2V13.8C66.9 6.5 72.8.6 80.1.6c7.3 0 13.2 5.9 13.2 13.2v33.1z" />
    <path fill="#ECB22E" d="M80.1 99.8c7.3 0 13.2 5.9 13.2 13.2 0 7.3-5.9 13.2-13.2 13.2-7.3 0-13.2-5.9-13.2-13.2V99.8h13.2zm0-6.6c-7.3 0-13.2-5.9-13.2-13.2 0-7.3 5.9-13.2 13.2-13.2h33.1c7.3 0 13.2 5.9 13.2 13.2 0 7.3-5.9 13.2-13.2 13.2H80.1z" />
  </svg>,
  telegram: p => <svg viewBox="0 0 24 24" {...p}>
    <circle cx="12" cy="12" r="11" fill="#FFFFFF" />
    <path fill="#26A5E4" d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.48.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z" />
  </svg>,
  whatsapp: p => <svg viewBox="0 0 24 24" {...p}>
    <path fill="#25D366" d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413Z" />
  </svg>,
  teams: p => <TeamsMark {...p} />,
}

/** The logo of a channel kind. Next to a visible label it is hidden from screen readers; pass `standalone` when it is
 *  shown alone, so it gets the kind's name. Unknown kinds get a generic icon. */
export function ChannelLogo({ kind, className, standalone }: { kind: string; className?: string; standalone?: boolean }) {
  const { t } = useTranslation()
  const a11y = standalone ? { role: 'img', 'aria-label': t(`approvals.kind.${kind}`, { defaultValue: kind }) } : { 'aria-hidden': true as const }
  const cls = cn('size-4 shrink-0', className)
  const M = MARKS[kind]
  if (M) return <M className={cls} data-channel-logo={kind} {...a11y} />
  const Icon = kind === 'email' ? Mail : MessageSquare
  return <Icon className={cn('text-muted-foreground', cls)} data-channel-logo={kind} {...a11y} />
}
