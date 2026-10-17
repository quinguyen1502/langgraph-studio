import { createHmac } from 'crypto'
import { test, expect, type Page } from '@playwright/test'
// TASK-0022: connect Slack, link my Slack account, pick the channel on a Human node, see the request in the audit log.
// Slack/Telegram are the fake APIs of backend/tests/fixtures/mock_chat_api.py (CHAT port), which record every message,
// so the test reads the verification code the "bot" sent and the approval request it posted.
const WF = {
  name: `Channel approval e2e ${Date.now()}`, state: [{ name: 'message', type: 'string' }, { name: 'decision', type: 'string' }],
  nodes: [{ id: 's', type: 'start', position: { x: 40, y: 150 }, data: { label: 'Start' } },
    { id: 'ask', type: 'human', position: { x: 300, y: 150 }, data: { label: 'Manager approval', prompt: 'Approve refund?', output_field: 'decision' } },
    { id: 'e', type: 'end', position: { x: 560, y: 150 }, data: { label: 'End' } }],
  edges: [{ id: '1', source: 's', target: 'ask' }, { id: '2', source: 'ask', target: 'e' }],
}
const CHAT = 'http://127.0.0.1:8111'
async function sent(page: Page, method: string, match: (b: any) => boolean) {
  let found: any = null
  await expect.poll(async () => { const calls = await (await page.request.get(`${CHAT}/_messages`)).json(); found = calls.filter((c: any) => c.method === method && match(c.body)).pop(); return !!found }).toBe(true)
  return found.body
}
async function login(page: Page) {
  await page.goto('/login'); await page.getByLabel('Mật khẩu', { exact: true }).fill('admin123'); await page.locator('#auth-submit').click()
  await expect(page).toHaveURL(/\/workflows$/)
  return page.evaluate(() => localStorage.getItem('token'))
}

test('approval channels: org connection, verified account, Human node, request, audit', async ({ page }) => {
  const token = await login(page); const auth = { Authorization: `Bearer ${token}` }
  const wid = (await (await page.request.post('/api/workflows', { headers: auth, data: WF })).json()).data.id
  await page.goto(`/workflows/${wid}`)
  // node settings: Studio only by default; nothing connected yet
  await page.locator('.react-flow__node[data-id="ask"]').click()
  await expect(page.locator('#approval-channel')).toContainText('Chỉ trong Studio')
  await expect(page.locator('#approval-no-channels')).toBeVisible()
  // connect Slack for the whole organization (the demo user is an admin)
  await page.locator('#user-menu').click(); await page.locator('#approval-channels-item').click()
  const dlg = page.locator('#approvals-dialog'); await expect(dlg).toBeVisible()
  await expect(dlg.locator('#channels-empty')).toBeVisible()
  const save = dlg.locator('#add-save'); await expect(save).toBeDisabled()
  await dlg.locator('#add-scope').click(); await page.getByRole('option', { name: 'Toàn tổ chức' }).click()
  await dlg.locator('#add-name').fill('Acme')
  await dlg.locator('#add-slack-bot_token').fill('nope'); await dlg.locator('#add-slack-signing_secret').fill('0123456789abcdef0123456789abcdef'); await save.click()
  await expect(dlg.getByRole('alert')).toContainText('bot_token')  // CHANNEL_CONFIG_INVALID, translated
  await dlg.locator('#add-slack-bot_token').fill('xoxb-1111-2222-e2etoken'); await save.click()
  const card = dlg.locator('[data-testid=channel-slack-org]')
  await expect(card).toContainText('••••oken'); await expect(card).toContainText('Toàn tổ chức'); await expect(card).toContainText('Acme')
  await expect(card.locator('input[readonly]')).toHaveValue(/\/api\/approvals\/callback\/slack$/)  // shared URL, routed by team_id
  await expect(card).toContainText('(2222)')  // workspace id read with auth.test
  const cid = await card.getAttribute('data-channel-id')
  // my accounts: link -> the bot DMs a code -> wrong code refused -> right code verifies
  await dlg.locator('#approvals-tab-accounts').click()
  await dlg.locator('#id-slack').fill('lower-case'); await dlg.locator('#id-slack-link').click()
  await expect(dlg.getByRole('alert')).toContainText('Slack')  // IDENTITY_INVALID
  await dlg.locator('#id-slack').fill('U0E2EADMIN'); await dlg.locator('#id-slack-link').click()
  await expect(dlg.locator('[data-testid=identity-slack]')).toContainText('Nhập mã 6 số')
  const code = (await sent(page, 'chat.postMessage', b => b.channel === 'U0E2EADMIN')).text.match(/\d{6}/)[0]
  await dlg.locator('#id-slack-code').fill(code === '000000' ? '111111' : '000000'); await dlg.locator('#id-slack-verify').click()
  await expect(dlg.getByRole('alert')).toContainText('còn 4 lần')  // IDENTITY_CODE_INVALID {left}
  await dlg.locator('#id-slack-code').fill(code); await dlg.locator('#id-slack-verify').click()
  await expect(dlg.locator('#id-slack-verified')).toBeVisible()
  await page.keyboard.press('Escape')
  // reopen the editor (channels reload) and configure the node
  await page.reload(); await page.locator('.react-flow__node[data-id="ask"]').click()
  await page.locator('#approval-channel').click(); await page.getByRole('option', { name: 'Slack · Acme · Toàn tổ chức' }).click()
  await expect(page.locator('#approval-not-connected')).toHaveCount(0)
  await page.locator('#approval-target').fill('C0E2E'); await page.locator('#approval-approvers').fill('lead@example.com, ops@example.com')
  await expect(page.locator('#approval-approvers')).toHaveValue('lead@example.com, ops@example.com')
  await page.getByRole('button', { name: 'Lưu', exact: true }).click()
  await expect.poll(async () => (await (await page.request.get(`/api/workflows/${wid}`, { headers: auth })).json()).data.nodes.find((n: any) => n.id === 'ask').data.approval)
    .toEqual({ channel_id: cid, channel: 'slack', target: 'C0E2E', approvers: ['lead@example.com', 'ops@example.com'] })
  // a run that pauses there posts the request (to the fake Slack API) and audits it
  await page.locator('#run-btn').click()
  await expect(page.locator('#trace-summary')).toHaveAttribute('data-status', 'waiting', { timeout: 30_000 })
  await page.locator('#user-menu').click(); await page.locator('#approval-channels-item').click(); await dlg.locator('#approvals-tab-audit').click()
  const row = dlg.locator('[data-testid=audit-row]', { hasText: WF.name }).first()
  await expect(row).toContainText('Đã gửi')
  const post = await sent(page, 'chat.postMessage', b => b.channel === 'C0E2E')
  expect(post.blocks[1].elements.map((e: any) => e.action_id)).toEqual(['approve', 'reject'])
  // Slack calls the shared URL when U0E2EADMIN (verified above, the run owner) presses Approve
  const body = new URLSearchParams({ payload: JSON.stringify({ type: 'block_actions', team: { id: '2222' }, user: { id: 'U0E2EADMIN' }, actions: [{ action_id: 'approve', value: post.blocks[1].elements[0].value }] }) }).toString()
  const ts = String(Math.floor(Date.now() / 1000)), sig = 'v0=' + createHmac('sha256', '0123456789abcdef0123456789abcdef').update(`v0:${ts}:${body}`).digest('hex')
  const res = await page.request.post('/api/approvals/callback/slack', { data: body, headers: { 'Content-Type': 'application/x-www-form-urlencoded', 'X-Slack-Request-Timestamp': ts, 'X-Slack-Signature': sig } })
  expect((await res.json()).data).toEqual({ outcome: 'approved' })
  await expect.poll(async () => (await (await page.request.get(`/api/workflows/${wid}/runs`, { headers: auth })).json()).data[0].status, { timeout: 30_000 }).toBe('ok')
  expect((await sent(page, 'chat.update', b => b.channel === 'C0E2E')).text).toContain('admin@example.com')
  await page.keyboard.press('Escape'); await page.locator('#user-menu').click(); await page.locator('#approval-channels-item').click(); await dlg.locator('#approvals-tab-audit').click()
  await expect(dlg.locator('[data-testid=audit-row]', { hasText: WF.name }).first()).toContainText('Đã duyệt')
})
