import { test, expect, type Page } from '@playwright/test'
import { apiToken } from './helpers'
// TASK-0067: workflow tests. Add a test case with a Human answer and a check, Run all, see it pass; change the check,
// see it fail with the expected and actual values; the test runs show under History > Test runs only.
const APPROVAL = {
  name: `Tests e2e ${Date.now()}`, state: [{ name: 'message', type: 'string' }, { name: 'decision', type: 'string' }],
  nodes: [{ id: 's', type: 'start', position: { x: 40, y: 150 }, data: { label: 'Start' } },
    { id: 'ask', type: 'human', position: { x: 260, y: 150 }, data: { label: 'Manager approval', prompt: 'Approve {{state.message}}?', output_field: 'decision' } },
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

async function pick(page: Page, trigger: ReturnType<Page['locator']>, option: string) {
  await trigger.click(); await page.getByRole('option', { name: option, exact: true }).click()
}

test('workflow tests: add a case, run all, see pass and fail with expected and actual', async ({ page }) => {
  const token = await login(page)
  const wid = (await (await page.request.post('/api/workflows', { headers: { Authorization: `Bearer ${token}` }, data: APPROVAL })).json()).data.id
  await page.goto(`/workflows/${wid}`)
  await page.locator('#tests-tab').click()
  await expect(page.locator('#tests-panel')).toContainText('Chưa có test case')

  await page.locator('#tests-add').click()
  const dlg = page.locator('#test-dialog')
  await dlg.locator('#test-name').fill('Duyệt hoàn tiền')
  await dlg.locator('#test-input').fill('{"message": "order A100"}')
  await dlg.getByTestId('answer-add').click()  // Approve by default
  await dlg.getByTestId('check-add').click()
  const check = dlg.getByTestId('check-edit').nth(1)
  await pick(page, check.getByTestId('check-field'), 'decision')
  await check.getByTestId('check-value').fill('approved')
  await dlg.locator('#test-save').click()
  await expect(dlg).toHaveCount(0)

  await page.locator('#tests-run-all').click()
  const row = page.getByTestId('test-row').filter({ hasText: 'Duyệt hoàn tiền' })
  await expect(row.getByTestId('test-status')).toHaveText('Đạt', { timeout: 30_000 })
  await expect(page.locator('#tests-summary')).toContainText('1 đạt, 0 không đạt trên v1')
  await expect(page.getByTestId('check-row')).toHaveCount(2)

  // the same case expecting "rejected" fails, and shows what it got
  await page.getByTestId('test-edit').click()
  await page.locator('#test-dialog').getByTestId('check-value').fill('rejected')
  await page.locator('#test-save').click()
  await page.locator('#tests-run-all').click()
  await expect(page.getByTestId('result-status')).toHaveText('Không đạt', { timeout: 30_000 })
  const failed = page.getByTestId('check-row').nth(1)
  await expect(failed).toContainText('rejected'); await expect(failed).toContainText('approved')

  // test runs stay out of the history unless asked for, and open in the trace
  await page.getByRole('tab', { name: 'Lịch sử' }).click()
  await expect(page.getByTestId('history-row')).toHaveCount(0)
  await page.locator('#history-tests').click()
  await expect(page.getByTestId('history-row')).toHaveCount(2)
  await expect(page.getByTestId('history-source').first()).toHaveText('Test')
  await page.locator('#tests-tab').click()
  await page.getByTestId('result-open-run').click()
  await expect(page.locator('#trace-summary')).toHaveAttribute('data-status', 'ok')
})
