/** RBAC (TASK-0014): the signed-in user's role and permissions (GET /api/me), shared by every page. */
import { useEffect, useState } from 'react'
import { api } from '@/lib/api'

export type Role = 'admin' | 'editor' | 'viewer'
export type Access = 'owner' | 'editor' | 'viewer'
export type Me = { id: string; email: string; role: Role; permissions: string[]; is_admin: boolean }
export type Share = { user_id: string; email: string; role: 'viewer' | 'editor'; created: number }
export type Shares = { owner: { id: string; email: string | null }; can_share: boolean; shares: Share[] }
export type AdminUser = { id: string; email: string; role: Role; active: boolean; created: number | null; workflows: number }
export type RoleMatrix = { roles: { role: Role; permissions: string[] }[]; permissions: string[]; workflow_access: { access: Access; actions: string[] }[] }

let cached: Promise<Me> | null = null
export const loadMe = (fresh = false) => (!cached || fresh ? (cached = api<Me>('/api/me').catch(e => { cached = null; throw e })) : cached)

export function useMe(): Me | null {
  const [me, setMe] = useState<Me | null>(null)
  useEffect(() => { let live = true; loadMe().then(m => live && setMe(m)).catch(() => {}); return () => { live = false } }, [])
  return me
}

export const can = (me: Me | null, permission: string) => !!me?.permissions.includes(permission)
export const canEdit = (a?: Access | null) => a === 'owner' || a === 'editor'
