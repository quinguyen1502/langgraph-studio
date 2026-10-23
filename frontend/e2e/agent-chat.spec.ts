import { test, expect, type Page } from '@playwright/test'
import { login, newWorkflow, N } from './helpers'
// TASK-0085 (REQ-0048 phase 1): the editor's Chat tab. Multi-turn memory through the conversation field, a Human node
// answered by the person chatting (and one left to a reviewer), and the step visibility modes.
const STATE = [{ name: 'message', type: 'string' }, { name: 'messages', type: 'list' }, { name: 'reply', type: 'string' }, { name: 'ok', type: 'string' }]
const ECHO = (name: string) => ({ name, state: STATE,
  nodes: [N('s', 'start', 40), N('bot', 'llm', 300, { label: 'Bot', model: 'gpt-4o-mini', prompt: 'History:\n{{state.messages}}', output_field: 'reply' }), N('e', 'end', 560)],
  edges: [{ id: '1', source: 's', target: 'bot' }, { id: '2', source: 'bot', target: 'e' }] })
const ASK = (name: string, by: 'visitor' | 'reviewer') => ({ name, state: STATE,
  nodes: [N('s', 'start', 40), N('ask', 'human', 260, { label: 'Confirm', prompt: 'Sure about {{state.message}}?', output_field: 'ok', answered_by: by }),
    N('bot', 'llm', 480, { label: 'Bot', model: 'gpt-4o-mini', prompt: 'Answer {{state.ok}}', output_field: 'reply' }), N('e', 'end', 700)],
  edges: [{ id: '1', source: 's', target: 'ask' }, { id: '2', source: 'ask', target: 'bot' }, { id: '3', source: 'bot', target: 'e' }] })

async function openChat(page: Page, wid: string) {
  await page.goto(`/workflows/${wid}`); await page.locator('#chat-tab').click(); await expect(page.locator('#chat-panel')).toBeVisible()
}
async function say(page: Page, text: string) {
  await page.locator('#chat-input').fill(text); await page.keyboard.press('Enter')
  await expect(page.getByTestId('chat-mine').last()).toHaveText(text)
}
const enable = (page: Page, H: Record<string, string>, wid: string, extra: Record<string, unknown> = {}) =>
  page.request.put(`/api/workflows/${wid}/chat`, { headers: H, data: { enabled: true, ...extra } })

test('chat remembers the conversation across turns', async ({ page }) => {
  const H = await login(page); const wid = await newWorkflow(page, H, ECHO(`Chat ${Date.now()}`))
  await openChat(page, wid)
  await expect(page.locator('#chat-off')).toBeVisible()
  await page.locator('#chat-turn-on').click()
  await expect(page.locator('#chat-messages_field')).toContainText('messages')   // guessed from the state
  await page.locator('#chat-enabled').click(); await page.locator('#chat-settings-save').click()
  await expect(page.locator('#chat-settings')).toHaveCount(0)

  await say(page, 'hello one')
  await expect(page.getByTestId('chat-answer').last()).toHaveAttribute('data-status', 'ok', { timeout: 20_000 })
  await expect(page.getByTestId('chat-session').first()).toContainText('hello one')
  await say(page, 'and two')
  await expect(page.getByTestId('chat-answer')).toHaveCount(2, { timeout: 20_000 })
  const last = page.getByTestId('chat-answer').last()
  await expect(last).toHaveAttribute('data-status', 'ok'); await expect(last).toContainText('hello one'); await expect(last).toContainText('and two')

  // a new chat starts without memory; the old one stays in the list
  await page.locator('#chat-new').click(); await expect(page.locator('#chat-empty')).toBeVisible()
  await say(page, 'fresh start')
  await expect(page.getByTestId('chat-answer').last()).toHaveAttribute('data-status', 'ok', { timeout: 20_000 })
  await expect(page.getByTestId('chat-answer').last()).not.toContainText('hello one')
  await expect(page.getByTestId('chat-session')).toHaveCount(2)
})

test('the person chatting answers a Human node in the chat; a reviewer step waits for Approvals', async ({ page }) => {
  const H = await login(page)
  const wid = await newWorkflow(page, H, ASK(`Ask ${Date.now()}`, 'visitor')); await enable(page, H, wid)
  await openChat(page, wid)
  await say(page, 'refund A1')
  await expect(page.locator('#chat-confirmation')).toBeVisible({ timeout: 20_000 })
  await expect(page.getByTestId('chat-answer').last()).toContainText('Sure about refund A1?')
  await page.locator('#chat-confirmation').getByTestId('answer-approve').click()
  await expect(page.getByTestId('chat-mine').last()).toHaveText('approved')
  await expect(page.getByTestId('chat-answer').last()).toContainText('Answer approved', { timeout: 20_000 })
  await expect(page.locator('#chat-confirmation')).toHaveCount(0)

  // the node's "Answered by" option in the config panel
  await page.locator('.react-flow__node[data-id="ask"]').click()
  await expect(page.locator('#human-answered-by')).toContainText('Người chat')

  const rid = await newWorkflow(page, H, ASK(`Review ${Date.now()}`, 'reviewer')); await enable(page, H, rid)
  await openChat(page, rid)
  await say(page, 'refund B2')
  await expect(page.locator('#chat-waiting-reviewer')).toBeVisible({ timeout: 20_000 })
  await expect(page.locator('#chat-confirmation')).toHaveCount(0)
})

test('step visibility: builders see every step, visitors what the settings allow', async ({ page }) => {
  const H = await login(page); const wid = await newWorkflow(page, H, ECHO(`Steps ${Date.now()}`))
  await enable(page, H, wid, { steps: 'labels' })
  await openChat(page, wid)
  await say(page, 'hi')
  await expect(page.getByTestId('chat-answer').last()).toHaveAttribute('data-status', 'ok', { timeout: 20_000 })
  const steps = page.getByTestId('chat-steps').last()
  await expect(steps).toHaveAttribute('data-mode', 'full'); await expect(steps.locator('[data-slot=trace-title]')).toHaveText(['Bot'])
  await steps.getByTestId('chat-step').click(); await expect(page.getByTestId('chat-step-detail')).toBeVisible()

  await page.locator('#chat-view-visitor').click()
  await expect(page.getByTestId('chat-steps').last()).toHaveAttribute('data-mode', 'labels')
  await expect(page.locator('[data-slot=trace-title]')).toHaveText(['Bot']); await expect(page.getByTestId('chat-step-detail')).toHaveCount(0)

  await enable(page, H, wid, { steps: 'none' })
  await page.locator('#chat-view-builder').click(); await page.locator('#chat-view-visitor').click()
  await expect(page.getByTestId('chat-answer').last()).toHaveAttribute('data-status', 'ok')
  await expect(page.getByTestId('chat-steps')).toHaveCount(0)
})
