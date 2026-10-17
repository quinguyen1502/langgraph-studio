import { test, expect, type Page } from '@playwright/test'
// TASK-0023: keyboard shortcuts in the editor and the cheat sheet.
async function login(page: Page) {
  await page.goto('/login'); await page.getByLabel('Email').fill('admin@example.com'); await page.getByLabel('Mật khẩu', { exact: true }).fill('admin123')
  await page.locator('#auth-submit').click(); await expect(page).toHaveURL(/\/workflows$/)
  return { Authorization: `Bearer ${await page.evaluate(() => localStorage.getItem('token'))}` }
}
const N = (id: string, type: string, x: number, data: Record<string, unknown> = {}) => ({ id, type, position: { x, y: 120 }, data: { label: id, ...data } })
export const SIMPLE = (name: string) => ({ name, state: [{ name: 'message', type: 'string' }, { name: 'answer', type: 'string' }],
  nodes: [N('start', 'start', 40), N('reply', 'llm', 300, { label: 'Reply', model: 'gpt-4o-mini', prompt: 'Answer {{state.message}}', output_field: 'answer' }), N('end', 'end', 560)],
  edges: [{ id: 'e1', source: 'start', target: 'reply' }, { id: 'e2', source: 'reply', target: 'end' }] })

test('save, run, delete with the keyboard; typing is safe; cheat sheet lists every shortcut', async ({ page }) => {
  const H = await login(page)
  const wid = (await (await page.request.post('/api/workflows', { headers: H, data: SIMPLE(`Keys ${Date.now()}`) })).json()).data.id
  await page.goto(`/workflows/${wid}`); await expect(page.locator('.react-flow__node')).toHaveCount(3)
  // Mod+S saves from inside the name field (no browser dialog)
  const renamed = `Keys renamed ${Date.now()}`
  await page.locator('header input').first().fill(renamed); await page.keyboard.press('Control+s')
  await expect.poll(async () => (await (await page.request.get(`/api/workflows/${wid}`, { headers: H })).json()).data.name).toBe(renamed)
  // Delete inside a text field edits text, not the graph
  await page.locator('.react-flow__node[data-id="reply"]').click()
  const label = page.locator('aside').last().locator('input').first(); await label.click(); await label.press('End'); await label.press('Backspace')
  await expect(page.locator('.react-flow__node')).toHaveCount(3)
  // Start/End are protected; a selected LLM node goes
  await page.locator('.react-flow__node[data-id="start"]').click(); await page.keyboard.press('Delete')
  await expect(page.locator('.react-flow__node[data-id="start"]')).toHaveCount(1)
  await page.locator('.react-flow__node[data-id="reply"]').click(); await page.keyboard.press('Delete')
  await expect(page.locator('.react-flow__node[data-id="reply"]')).toHaveCount(0)
  await expect(page.locator('.react-flow__edge')).toHaveCount(0)
  // Mod+Enter runs (start → end directly is invalid without edges; the run still starts and reports)
  await page.locator('.react-flow__pane').click(); await page.keyboard.press('Control+Enter')
  await expect(page.locator('[role=tab][id$="-trigger-logs"]')).toHaveAttribute('data-state', 'active')
  // ? opens the cheat sheet
  await page.locator('.react-flow__pane').click(); await page.keyboard.press('Shift+?')
  const sheet = page.locator('#shortcut-cheatsheet'); await expect(sheet).toBeVisible()
  await expect(sheet.getByTestId('shortcut-row')).toHaveCount(10)
  await expect(sheet).toContainText('Ctrl'); await expect(sheet).toContainText('Lưu workflow')
  await page.keyboard.press('Escape'); await expect(sheet).toHaveCount(0)
})
