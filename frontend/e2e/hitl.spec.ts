import { test, expect, type Page } from '@playwright/test'
import { apiToken } from './helpers'
// TASK-0006: a run pauses at a Human node, shows up as pending, and resumes from the panel.
const APPROVAL = {
  name: `Approval e2e ${Date.now()}`, state: [{ name: 'message', type: 'string' }, { name: 'decision', type: 'string' }],
  nodes: [{ id: 's', type: 'start', position: { x: 40, y: 150 }, data: { label: 'Start' } },
    { id: 'ask', type: 'human', position: { x: 260, y: 150 }, data: { label: 'Manager approval', prompt: 'Approve refund for {{state.message}}?', output_field: 'decision' } },
    { id: 'route', type: 'condition', position: { x: 500, y: 150 }, data: { label: 'Approved?', field: 'decision', default: 'rejected' } },
    { id: 'e', type: 'end', position: { x: 740, y: 150 }, data: { label: 'End' } }],
  edges: [{ id: '1', source: 's', target: 'ask' }, { id: '2', source: 'ask', target: 'route' },
    { id: '3', source: 'route', target: 'e', label: 'approved' }, { id: '4', source: 'route', target: 'e', label: 'rejected' }],
}
async function login(page: Page) {
  await page.goto('/login'); await page.getByLabel('Mật khẩu', { exact: true }).fill('admin123'); await page.locator('#auth-submit').click()
  await expect(page).toHaveURL(/\/workflows$/)
  return apiToken(page)
}

test('human node: wait, pending list, approve, complete', async ({ page }) => {
  const token = await login(page)
  const wid = (await (await page.request.post('/api/workflows', { headers: { Authorization: `Bearer ${token}` }, data: APPROVAL })).json()).data.id
  await page.goto(`/workflows/${wid}`)
  await page.locator('.react-flow__node[data-id="ask"]').click()
  await expect(page.locator('#human-prompt')).toHaveText('Approve refund for message?'); await expect(page.locator('#human-prompt .template-tag[data-field="message"]')).toBeVisible()
  await page.getByRole('tab', { name: 'Input' }).first().click()
  await page.locator('#run-input').fill('{"message": "order A100"}')
  await page.locator('#run-btn').click()
  await expect(page.locator('#trace-summary')).toHaveAttribute('data-status', 'waiting', { timeout: 30_000 })
  await expect(page.locator('#human-question')).toHaveText('Approve refund for order A100?')
  // pending list on the workflows page links back to the run
  await page.goto('/workflows')
  await expect(page.locator('[data-testid=pending-count]')).toBeVisible()  // header badge (TASK-0019)
  expect(Number(await page.locator('[data-testid=pending-count]').textContent())).toBeGreaterThan(0)
  const row = page.locator('[data-testid=pending-row]', { hasText: APPROVAL.name }); await expect(row).toBeVisible()
  await row.getByRole('button').click()
  await expect(page).toHaveURL(new RegExp(`/workflows/${wid}\\?run=`))
  await expect(page.locator('#human-panel')).toBeVisible()
  await page.locator('#human-approve').click()
  await expect(page.locator('#trace-summary')).toHaveAttribute('data-status', 'ok', { timeout: 30_000 })
  await expect(page.locator('#human-panel')).toHaveCount(0)
  await expect(page.locator('.trace-row[data-span="ask#1"]')).toHaveCount(1) // the resumed Human node keeps one span
  await page.goto('/workflows'); await expect(page.locator('[data-testid=pending-row]', { hasText: APPROVAL.name })).toHaveCount(0)
})
