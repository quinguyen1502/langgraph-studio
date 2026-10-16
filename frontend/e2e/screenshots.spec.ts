// Captures docs/screenshots for TASK-0003 states. Run: SHOTS=1 npm run e2e -- screenshots
import { test, expect } from '@playwright/test'
test.skip(!process.env.SHOTS, 'set SHOTS=1 to capture screenshots')
const out = (n: string) => `../docs/screenshots/${n}.png`
test.use({ viewport: { width: 1280, height: 800 } })

test('capture auth and list states', async ({ page, request }) => {
  const email = `shots-${Date.now()}@example.com`
  await page.goto('/login?expired=1&next=%2Fworkflows'); await expect(page.locator('#expired-notice')).toBeVisible()
  await page.screenshot({ path: out('auth-expired-notice') })
  await page.getByLabel('Mật khẩu', { exact: true }).fill('wrongpass1'); await page.locator('#auth-submit').click()
  await expect(page.locator('#auth-error')).toBeVisible(); await expect(page.locator('#auth-submit')).toBeEnabled(); await page.mouse.move(0, 0); await page.waitForTimeout(400)
  await page.screenshot({ path: out('auth-login-error') })
  await page.goto('/register'); await page.getByLabel('Email').fill(email)
  await page.getByLabel('Mật khẩu', { exact: true }).fill('abcdefg'); await page.getByLabel('Xác nhận mật khẩu').fill('abcdefx')
  await page.screenshot({ path: out('auth-register-password-rules') })
  const r = await request.post('/api/auth/register', { data: { email, password: 'goodpass1' } }); const { token, user } = await r.json()
  const H = { Authorization: `Bearer ${token}` }
  for (const w of await (await request.get('/api/workflows', { headers: H })).json()) await request.delete(`/api/workflows/${w.id}`, { headers: H })
  await page.evaluate(([t, u]) => { localStorage.setItem('token', t); localStorage.setItem('user', JSON.stringify(u)) }, [token, user] as const)
  await page.goto('/workflows'); await expect(page.locator('#wf-empty')).toBeVisible(); await page.screenshot({ path: out('list-empty-state') })
  await request.post('/api/workflows', { headers: H, data: { name: 'A very long workflow name that keeps going to show truncation in the list view without breaking the table layout at all', nodes: [], edges: [] } })
  await request.post('/api/workflows', { headers: H, data: { name: 'Support triage', nodes: [], edges: [] } })
  await page.reload(); await page.screenshot({ path: out('list-long-names') })
  await page.locator('.wf-actions').first().click(); await page.getByRole('menuitem', { name: 'Đổi tên', exact: true }).click()
  await page.locator('#rename-input').fill('   '); await page.screenshot({ path: out('list-rename-empty-error') }); await page.keyboard.press('Escape')
  await page.locator('#wf-search').fill('nothing matches'); await expect(page.locator('#wf-no-results')).toBeVisible()
  await page.screenshot({ path: out('list-search-no-results') })
  await page.evaluate(() => localStorage.setItem('theme', 'dark')); await page.reload(); await page.locator('#wf-search').fill('nothing matches')
  await page.screenshot({ path: out('list-search-no-results-dark') })
  await page.evaluate(() => localStorage.setItem('theme', 'light'))
  await page.goto('/workflows/doesnotexist'); await expect(page.locator('#editor-not-found')).toBeVisible()
  await page.screenshot({ path: out('editor-not-found') })
})
