import { test, expect, type Page } from '@playwright/test'
import { confirmDelete } from './confirm'

async function loginAdmin(page: Page) {
  await page.goto('/login'); await page.getByLabel('Mật khẩu', { exact: true }).fill('admin123'); await page.locator('#auth-submit').click()
  await expect(page).toHaveURL(/\/workflows$/)
}

test('credentials: add (masked), invalid base URL error, pick on LLM node, delete', async ({ page }) => {
  const name = `e2e-${Date.now()}`
  await loginAdmin(page)
  await page.locator('#creds-btn').click()
  const dlg = page.getByRole('dialog')
  await dlg.getByPlaceholder('OpenAI cá nhân').fill(name)
  await dlg.locator('input[type=password]').fill('sk-e2e-secret-9876')
  await dlg.getByPlaceholder('https://api.openai.com/v1').fill('ftp://bad')
  await dlg.getByRole('button', { name: 'Thêm credential' }).click()
  await expect(dlg.locator('#cred-error')).toContainText('http(s)://')
  await dlg.getByPlaceholder('https://api.openai.com/v1').fill('')
  await dlg.getByRole('button', { name: 'Thêm credential' }).click()
  const row = dlg.locator('div.rounded-md', { hasText: name })
  await expect(row).toContainText('••••9876')
  await expect(dlg).not.toContainText('sk-e2e-secret-9876')
  await page.keyboard.press('Escape')

  await page.goto('/workflows/example')
  await page.locator('.react-flow__node[data-id="classify"]').click()
  await page.locator('#llm-credential').click()
  await expect(page.getByRole('option', { name: new RegExp(name) })).toBeVisible()
  await page.keyboard.press('Escape')

  await page.goto('/workflows'); await page.locator('#creds-btn').click()
  await page.getByRole('dialog').getByRole('button', { name: `Xoá ${name}` }).click(); await confirmDelete(page, name)
  await expect(page.getByRole('dialog')).not.toContainText(name)
})
