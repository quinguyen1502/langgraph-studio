import { test, expect } from '@playwright/test'

test.use({ locale: 'en-US' })

test('language: defaults from browser, switches on login + app header, persists', async ({ page }) => {
  await page.goto('/login')
  await expect(page.locator('#auth-submit')).toHaveText('Sign in')
  await expect(page.locator('html')).toHaveAttribute('lang', 'en')
  await page.locator('#lang-switch').click(); await page.locator('[data-lang="vi"]').click()
  await expect(page.locator('#auth-submit')).toHaveText('Đăng nhập')
  await page.reload()
  await expect(page.locator('#auth-submit')).toHaveText('Đăng nhập')
  expect(await page.evaluate(() => localStorage.getItem('lang'))).toBe('vi')

  await page.getByLabel('Mật khẩu', { exact: true }).fill('admin123'); await page.locator('#auth-submit').click()
  await expect(page).toHaveURL(/\/workflows$/)
  await expect(page.locator('#new-wf')).toContainText('Workflow mới')
  await page.locator('#lang-switch').click(); await page.locator('[data-lang="en"]').click()
  await expect(page.locator('#new-wf')).toContainText('New workflow')
  await expect(page.getByRole('columnheader', { name: 'Last run' })).toBeVisible()
  await page.goto('/workflows/example')
  await expect(page.locator('#run-btn')).toContainText('Run')
  await expect(page.locator('#history-all')).toBeVisible()
})

test('error codes are translated (fallback to the English server message)', async ({ page }) => {
  await page.goto('/login')
  await page.getByLabel('Password', { exact: true }).fill('wrong-pass1'); await page.locator('#auth-submit').click()
  await expect(page.locator('#auth-error')).toHaveText('Incorrect email or password')
  await page.locator('#lang-switch').click(); await page.locator('[data-lang="vi"]').click()
  await page.locator('#auth-submit').click()
  await expect(page.locator('#auth-error')).toHaveText('Sai email hoặc mật khẩu') // AUTH_INVALID_CREDENTIALS from vi.json

  // unknown code → falls back to the server's English message
  await page.route('**/api/auth/login', r => r.fulfill({ status: 418, contentType: 'application/json',
    body: JSON.stringify({ success: false, data: null, error: { code: 'SOMETHING_NEW', message: 'Server says no' } }) }))
  await page.locator('#auth-submit').click()
  await expect(page.locator('#auth-error')).toHaveText('Server says no')
})
