/** Approval channels API types (TASK-0022). */
import type { TFunction } from 'i18next'

export type ChannelKind = { kind: string; fields: string[]; optional: string[] }
export type Channel = { id: string; kind: string; scope: 'user' | 'org'; name: string | null; team_id: string | null; hint: string; created: number; editable: boolean
  callback_url: string | null; callback_path: string; shared_callback_url: string | null; shared_callback_path: string | null }
export type Channels = { kinds: ChannelKind[]; channels: Channel[]; public_url: string | null; is_admin: boolean }

/** "Slack · Acme (org)" — what a connection is called in selects and cards. */
export function channelLabel(t: TFunction, c: Channel) {
  return [t(`approvals.kind.${c.kind}`), c.name, t(`approvals.scope.${c.scope}`)].filter(Boolean).join(' · ')
}
