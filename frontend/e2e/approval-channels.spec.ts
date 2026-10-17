import { test, expect, type Page } from '@playwright/test'
// TASK-0022: connect Slack, link my Slack account, pick the channel on a Human node, see the request in the audit log.
// The Slack API is unreachable here (SLACK_API_URL=http://127.0.0.1:9), so the request is audited as "send failed";
// signed callbacks with mocked Slack/Telegram APIs are covered by backend/tests/test_approval_channels.py.
const WF = {
  name: `Channel approval e2e ${Date.now()}`, state: [{ name: 'message', type: 'string' }, { name: 'decision', type: 'string' }],
  nodes: [{ id: 's', type: 'start', position: { x: 40, y: 150 }, data: { label: 'Start' } },
    { id: 'ask', type: 'human', position: { x: 300, y: 150 }, data: { label: 'Manager approval', prompt: 'Approve refund?', output_field: 'decision' } },
    { id: 'e', type: 'end', position: { x: 560, y: 150 }, data: { label: 'End' } }],
  edges: [{ id: '1', source: 's', target: 'ask' }, { id: '2', source: 'ask', target: 'e' }],
}
async function login(page: Page) {
  await page.goto('/login'); await page.getByLabel('Mật khẩu', { exact: true }).fill('admin123'); await page.locator('#auth-submit').click()
  await expect(page).toHaveURL(/\/workflows$/)
  return page.evaluate(() => localStorage.getItem('token'))
}

test('approval channels: connect, link account, configure the Human node, audit', async ({ page }) => {
  const token = await login(page); const auth = { Authorization: `Bearer ${token}` }
  const wid = (await (await page.request.post('/api/workflows', { headers: auth, data: WF })).json()).data.id
  await page.goto(`/workflows/${wid}`)
  // node settings: Studio only by default; Slack is "not connected" yet
  await page.locator('.react-flow__node[data-id="ask"]').click()
  await expect(page.locator('#approval-channel')).toContainText('Chỉ trong Studio')
  await page.locator('#approval-channel').click(); await page.getByRole('option', { name: /Slack · chưa kết nối/ }).click()
  await expect(page.locator('#approval-not-connected')).toBeVisible()
  // connect Slack in the dialog (user menu)
  await page.locator('#user-menu').click(); await page.locator('#approval-channels-item').click()
  const dlg = page.locator('#approvals-dialog'); await expect(dlg).toBeVisible()
  const save = dlg.locator('#ch-slack-save'); await expect(save).toBeDisabled()
  await dlg.locator('#ch-slack-bot_token').fill('nope'); await dlg.locator('#ch-slack-signing_secret').fill('0123456789abcdef0123456789abcdef'); await save.click()
  await expect(dlg.getByRole('alert')).toContainText('bot_token')  // CHANNEL_CONFIG_INVALID, translated
  await dlg.locator('#ch-slack-bot_token').fill('xoxb-1111-2222-e2etoken'); await save.click()
  await expect(dlg.locator('[data-testid=channel-slack]')).toContainText('••••oken')
  await expect(dlg.locator('#ch-slack-url')).toHaveValue(/\/api\/approvals\/callback\/slack\/[0-9a-f]{12}$/)
  // my accounts
  await dlg.locator('#approvals-tab-accounts').click()
  await dlg.locator('#id-slack').fill('lower-case'); await dlg.locator('#id-save').click()
  await expect(dlg.getByRole('alert')).toContainText('Slack')  // IDENTITY_INVALID
  await dlg.locator('#id-slack').fill('U0E2EADMIN'); await dlg.locator('#id-save').click(); await expect(dlg.locator('#id-saved')).toBeVisible()
  await page.keyboard.press('Escape')
  // reopen the editor (channels reload) and configure the node
  await page.reload(); await page.locator('.react-flow__node[data-id="ask"]').click()
  await page.locator('#approval-channel').click(); await page.getByRole('option', { name: 'Slack', exact: true }).click()
  await expect(page.locator('#approval-not-connected')).toHaveCount(0)
  await page.locator('#approval-target').fill('C0E2E'); await page.locator('#approval-approvers').fill('lead@example.com, ops@example.com')
  await expect(page.locator('#approval-approvers')).toHaveValue('lead@example.com, ops@example.com')
  await page.getByRole('button', { name: 'Lưu', exact: true }).click()
  await expect.poll(async () => (await (await page.request.get(`/api/workflows/${wid}`, { headers: auth })).json()).data.nodes.find((n: any) => n.id === 'ask').data.approval)
    .toEqual({ channel: 'slack', target: 'C0E2E', approvers: ['lead@example.com', 'ops@example.com'] })
  // a run that pauses there sends the request (audited; this Slack API is unreachable)
  await page.locator('#run-btn').click()
  await expect(page.locator('#trace-summary')).toHaveAttribute('data-status', 'waiting', { timeout: 30_000 })
  await page.locator('#user-menu').click(); await page.locator('#approval-channels-item').click(); await dlg.locator('#approvals-tab-audit').click()
  const row = dlg.locator('[data-testid=audit-row]', { hasText: WF.name }).first()
  await expect(row).toContainText('Gửi thất bại'); await expect(row).toContainText('Gọi API Slack thất bại')
})
