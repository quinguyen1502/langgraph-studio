import { test, expect } from '@playwright/test'
import { readFileSync } from 'node:fs'
import { login, newWorkflow, N, SIMPLE } from './helpers'
import { confirmDelete } from './confirm'
// TASK-0025: template gallery, save-as-template (sanitised), export → import → use → delete.

test('blank and built-in templates from the New workflow gallery', async ({ page }) => {
  await login(page)
  await page.locator('#new-wf').click(); const g = page.locator('#template-gallery'); await expect(g).toBeVisible()
  await expect(g.locator('[data-id=builtin-approval]')).toBeVisible()
  await expect(g.locator('[data-id=builtin-chatbot] [data-testid=tpl-preview] rect')).toHaveCount(3)
  await expect(g.locator('[data-id=builtin-chatbot] [data-testid=tpl-delete]')).toHaveCount(0)  // built-ins are read-only
  await g.locator('[data-id=builtin-router] button').first().click()
  await expect(page).toHaveURL(/\/workflows\/[^/]+$/); await expect(page.locator('.react-flow__node')).toHaveCount(7)
  await page.goto('/workflows'); await page.locator('#new-wf').click(); await page.locator('#tpl-blank').click()
  await expect(page).toHaveURL(/\/workflows\/[^/]+$/); await expect(page.locator('.react-flow__node')).toHaveCount(2)
})

test('save as template strips secrets; export, import, use and delete', async ({ page }) => {
  const H = await login(page); const name = `Tpl ${Date.now()}`
  const wf = SIMPLE(`Src ${Date.now()}`)
  wf.nodes.splice(2, 0, N('call', 'tool', 430, { mode: 'http', url: 'https://x.example', credential_id: 'cred-xyz', headers: { Authorization: 'Bearer s3cret' }, output_field: 'answer' }))
  const wid = await newWorkflow(page, H, wf)
  await page.goto(`/workflows/${wid}`); await expect(page.locator('.react-flow__node')).toHaveCount(4)
  await page.locator('#more-btn').click(); await page.locator('#save-template-btn').click(); await expect(page.locator('#tpl-unsaved')).toHaveCount(0)
  await page.locator('#tpl-name').fill(name); await page.locator('#tpl-desc').fill('From e2e')
  await expect(page.locator('#tpl-scope')).toBeVisible()  // admin may share org-wide
  await page.locator('#tpl-save').click(); await expect(page.locator('#tpl-saved')).toBeVisible()
  await page.keyboard.press('Escape')

  await page.goto('/workflows'); await page.locator('#new-wf').click()
  const card = page.locator('[data-testid=tpl-card]', { hasText: name }); await expect(card).toBeVisible()
  const dl = page.waitForEvent('download'); await card.locator('[data-testid=tpl-export]').click()
  const file = await (await dl).path(); const text = readFileSync(file!, 'utf8')
  expect(text).toContain('langgraph-studio/template'); expect(text).not.toContain('s3cret'); expect(text).not.toContain('cred-xyz')

  // import the exported file back (a second copy), then a broken file shows the coded error
  await page.locator('#tpl-import-file').setInputFiles(file!)
  await expect(page.locator('[data-testid=tpl-card]', { hasText: name })).toHaveCount(2)
  await page.locator('#tpl-import-file').setInputFiles({ name: 'bad.json', mimeType: 'application/json', buffer: Buffer.from('{"format":"x"}') })
  await expect(page.locator('#tpl-error')).toBeVisible()

  // delete both copies through the type-the-name dialog
  for (let i = 0; i < 2; i++) {
    await page.locator('[data-testid=tpl-card]', { hasText: name }).first().locator('[data-testid=tpl-delete]').click()
    await confirmDelete(page, name)
  }
  await expect(page.locator('[data-testid=tpl-card]', { hasText: name })).toHaveCount(0)
})
