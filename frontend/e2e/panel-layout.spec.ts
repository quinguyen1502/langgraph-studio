import { test, expect } from '@playwright/test'
import { login, newWorkflow, N } from './helpers'
import { expectRowAligned, expectBaselineAligned } from './helpers/alignment'
// TASK-0085: the bottom panel (Run · Test · Code; Run = input | logs, a run picker and "View all") and the Chat side
// panel (header button or Shift+C, 340–760px, width and open state remembered, fullscreen with Esc, Config beside it).
const STATE = [{ name: 'message', type: 'string' }, { name: 'messages', type: 'list' }, { name: 'reply', type: 'string' }]
const WF = (name: string) => ({ name, state: STATE,
  nodes: [N('s', 'start', 40), N('bot', 'llm', 300, { label: 'Bot', model: 'gpt-4o-mini', prompt: 'Reply to {{state.message}}', output_field: 'reply' }), N('e', 'end', 560)],
  edges: [{ id: '1', source: 's', target: 'bot' }, { id: '2', source: 'bot', target: 'e' }] })

test('Run mode: input beside the logs, the run picker and View all', async ({ page }) => {
  await page.setViewportSize({ width: 1600, height: 960 })
  const H = await login(page); const wid = await newWorkflow(page, H, WF(`Runs ${Date.now()}`))
  await page.goto(`/workflows/${wid}`)
  await expect(page.locator('#run-tab')).toHaveAttribute('data-state', 'active')
  await expect(page.locator('#run-input')).toBeVisible()
  for (let i = 0; i < 2; i++) { await page.locator('#run-btn').click(); await expect(page.locator('#trace-summary')).toHaveAttribute('data-status', 'ok', { timeout: 20_000 }) }
  await expect(page.locator('#run-input')).toBeVisible()                        // input stays beside the logs
  await expect(page.locator('#run-picker')).toContainText(/\d/)                  // the latest run is picked

  // one toolbar row: tabs, picker and View all share height and centre; time and id share a baseline
  await expectRowAligned([page.locator('#run-toolbar [role=tablist]'), page.locator('#run-picker'), page.locator('#history-all')], { label: 'run toolbar' })
  await expectBaselineAligned([page.locator('#run-picker [data-slot=run-time]'), page.locator('#run-picker [data-slot=run-id]')], { label: 'run picker' })

  await page.locator('#run-picker').click()
  await expect(page.getByRole('option')).toHaveCount(2)
  await page.getByRole('option').last().click()
  await expect(page.locator('#trace-summary')).toBeVisible()

  await page.locator('#history-all').click(); await expect(page.locator('#history-dialog')).toBeVisible()
  await expect(page.getByTestId('history-row')).toHaveCount(2)
  await page.getByTestId('history-row').first().click(); await expect(page.locator('#history-dialog')).toHaveCount(0)

  await page.locator('#tests-tab').click(); await expect(page.locator('#run-input')).toHaveCount(0)
  await page.locator('#code-tab').click(); await expect(page.locator('#code-tab')).toHaveAttribute('data-state', 'active')
  await page.locator('#run-tab').click(); await expect(page.locator('#run-input')).toBeVisible()
})

test('Chat side panel: toggle, width and open state remembered, fullscreen keeps the draft, Config beside it', async ({ page }) => {
  await page.setViewportSize({ width: 1600, height: 960 })
  const H = await login(page); const wid = await newWorkflow(page, H, WF(`Chat ${Date.now()}`))
  await page.request.put(`/api/workflows/${wid}/chat`, { headers: H, data: { enabled: true } })
  await page.goto(`/workflows/${wid}`)
  await expect(page.locator('#chat-side')).toHaveCount(0)
  await page.locator('#chat-open').click(); await expect(page.locator('#chat-side')).toBeVisible()
  await expect(page.locator('#chat-open')).toHaveAttribute('aria-pressed', 'true')
  const w0 = (await page.locator('#panel-chat').boundingBox())!.width
  expect(Math.abs(w0 - 420)).toBeLessThanOrEqual(2)

  // the chat toolbar and the editor header stay on one size each
  await expectRowAligned([page.locator('#chat-view'), page.locator('#chat-session-picker'), page.locator('#chat-new'), page.locator('#chat-fullscreen'), page.locator('#chat-close')], { label: 'chat toolbar' })
  await expectRowAligned([page.locator('#save-btn'), page.locator('#run-btn'), page.locator('#chat-open'), page.locator('#more-btn')], { label: 'editor header' })

  // Config stays beside the chat: a node can be edited while chatting
  await page.locator('.react-flow__node[data-id="bot"]').click(); await expect(page.locator('#config-panel')).toBeVisible()
  expect((await page.locator('#panel-right').boundingBox())!.width).toBeGreaterThan(200)

  // drag the chat border: 340–760px, remembered with the open state after a reload
  const h = (await page.locator('#resize-chat').boundingBox())!
  await page.mouse.move(h.x + h.width / 2, h.y + h.height / 2); await page.mouse.down()
  await page.mouse.move(h.x - 600, h.y + h.height / 2, { steps: 8 }); await page.mouse.up()
  const w1 = (await page.locator('#panel-chat').boundingBox())!.width
  expect(w1).toBeGreaterThan(740); expect(w1).toBeLessThanOrEqual(762)
  await page.reload(); await expect(page.locator('#chat-side')).toBeVisible()
  expect(Math.abs((await page.locator('#panel-chat').boundingBox())!.width - w1)).toBeLessThanOrEqual(2)

  // fullscreen keeps the conversation and the draft; Esc leaves it
  await page.locator('#chat-input').fill('draft kept')
  await page.locator('#chat-fullscreen').click(); await expect(page.locator('#chat-side')).toHaveAttribute('data-fullscreen', 'true')
  await expect(page.locator('#chat-input')).toHaveValue('draft kept')
  // fullscreen: the icon-only New chat sits in the sidebar header, level with the chat toolbar
  await expect(page.locator('#chat-new')).toHaveAttribute('aria-label', 'Chat mới'); await expect(page.locator('#chat-new')).toHaveText('')
  await expectRowAligned([page.locator('#chat-new'), page.locator('#chat-fullscreen'), page.locator('#chat-close')], { label: 'fullscreen chat header' })
  await expectRowAligned([page.locator('#chat-sidebar-header > span'), page.locator('#chat-new')], { sameHeight: false, label: 'chat sidebar header' })
  await page.keyboard.press('Escape'); await expect(page.locator('#chat-side')).not.toHaveAttribute('data-fullscreen', 'true')
  await expect(page.locator('#chat-input')).toHaveValue('draft kept')

  // × closes, Shift+C (on the canvas) toggles
  await page.locator('#chat-close').click(); await expect(page.locator('#chat-side')).toHaveCount(0)
  await page.locator('.react-flow__pane').click(); await page.keyboard.press('Shift+C'); await expect(page.locator('#chat-side')).toBeVisible()
  await page.locator('.react-flow__pane').click(); await page.keyboard.press('Shift+C'); await expect(page.locator('#chat-side')).toHaveCount(0)
  await page.reload(); await expect(page.locator('#run-btn')).toBeVisible(); await expect(page.locator('#chat-side')).toHaveCount(0)
})

test('narrow screens: Config folds away while nothing is selected', async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 860 })
  const H = await login(page); const wid = await newWorkflow(page, H, WF(`Narrow ${Date.now()}`))
  await page.goto(`/workflows/${wid}`)
  await expect.poll(async () => (await page.locator('#panel-right').boundingBox())?.width ?? 0).toBeGreaterThan(200)
  await page.locator('#chat-open').click(); await expect(page.locator('#chat-side')).toBeVisible()   // 1280 - 420 < 1100
  await expect.poll(async () => (await page.locator('#panel-right').boundingBox())?.width ?? 0).toBeLessThan(2)
  await page.locator('.react-flow__node[data-id="bot"]').click()
  await expect.poll(async () => (await page.locator('#panel-right').boundingBox())?.width ?? 0).toBeGreaterThan(200)
  await page.locator('.react-flow__pane').click({ position: { x: 30, y: 30 } })
  await expect.poll(async () => (await page.locator('#panel-right').boundingBox())?.width ?? 0).toBeLessThan(2)
})
