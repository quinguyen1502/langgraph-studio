import { expect, type Page } from '@playwright/test'
/** Shared e2e helpers for the Phase 5 editor specs. */
export async function login(page: Page, email = 'admin@example.com', password = 'admin123') {
  await page.goto('/login'); await page.getByLabel('Email').fill(email); await page.getByLabel('Mật khẩu', { exact: true }).fill(password)
  await page.locator('#auth-submit').click(); await expect(page).toHaveURL(/\/workflows$/)
  return { Authorization: `Bearer ${await page.evaluate(() => localStorage.getItem('token'))}` }
}
export const N = (id: string, type: string, x: number, data: Record<string, unknown> = {}, y = 120) => ({ id, type, position: { x, y }, data: { label: id, ...data } })
export const SIMPLE = (name: string) => ({ name, state: [{ name: 'message', type: 'string' }, { name: 'answer', type: 'string' }],
  nodes: [N('start', 'start', 40), N('reply', 'llm', 300, { label: 'Reply', model: 'gpt-4o-mini', prompt: 'Answer {{state.message}}', output_field: 'answer' }), N('end', 'end', 560)],
  edges: [{ id: 'e1', source: 'start', target: 'reply' }, { id: 'e2', source: 'reply', target: 'end' }] })
export async function newWorkflow(page: Page, H: Record<string, string>, data: unknown) {
  return (await (await page.request.post('/api/workflows', { headers: H, data })).json()).data.id as string
}
