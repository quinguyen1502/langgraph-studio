// Screenshots for the handbook (handbook/docs/<lang>/images/*.png).
// Run: HANDBOOK_SHOTS=1 npm run e2e -- handbook
// The Code node shots need Docker and the studio-code:1 image; they are skipped otherwise.
import { test, expect, type Page } from '@playwright/test'
import { N, signIn } from './helpers'

test.skip(!process.env.HANDBOOK_SHOTS, 'set HANDBOOK_SHOTS=1 to capture handbook screenshots')
test.use({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1.5 })
test.setTimeout(240_000)

type Lang = 'en' | 'vi'
const T = {
  en: {
    digest: 'Release notes digest', support: 'Customer Support', refund: 'Refund approval', normalize: 'Normalize webhook payload',
    start: 'Start', end: 'End', each: 'Each release', summarize: 'Summarize release', compose: 'Compose digest', send: 'Email the team',
    draft: 'Draft reply', approve: 'Manager approval', approved: 'Approved?', notify: 'Send refund email', clean: 'Clean payload',
    approvePrompt: 'Approve a refund of {{state.amount}} for order {{state.order_id}}?',
    morning: 'Morning digest', broken: 'Broken graph', refine: 'Refine', lonely: 'Unreachable tool',
    kb: 'Support FAQ', kbDesc: 'Shipping and refund answers', faq: 'Shipping\n\nOrders ship within two business days.\n\nRefunds\n\nRefunds reach the card within 7 days of the return.',
  },
  vi: {
    digest: 'Tổng hợp release notes', support: 'Customer Support', refund: 'Duyệt hoàn tiền', normalize: 'Chuẩn hoá payload webhook',
    start: 'Start', end: 'End', each: 'Từng release', summarize: 'Tóm tắt release', compose: 'Soạn bản tổng hợp', send: 'Gửi email cho team',
    draft: 'Soạn trả lời', approve: 'Quản lý duyệt', approved: 'Đã duyệt?', notify: 'Gửi email hoàn tiền', clean: 'Làm sạch payload',
    approvePrompt: 'Duyệt hoàn {{state.amount}} cho đơn {{state.order_id}}?',
    morning: 'Bản tổng hợp buổi sáng', broken: 'Graph lỗi', refine: 'Chỉnh lại', lonely: 'Tool không tới được',
    kb: 'FAQ hỗ trợ', kbDesc: 'Câu trả lời về giao hàng và hoàn tiền', faq: 'Giao hàng\n\nĐơn hàng được giao trong hai ngày làm việc.\n\nHoàn tiền\n\nTiền được hoàn về thẻ trong 7 ngày sau khi nhận hàng trả lại.',
  },
}

const CODE = `def main(state):
    event = state["payload"]
    print("event:", event["type"])
    return {
        "id": event["id"],
        "type": event["type"].lower(),
        "amount": round(event["amount_cents"] / 100, 2),
    }
`

const digest = (s: typeof T.en) => ({
  name: s.digest,
  state: [{ name: 'releases', type: 'list' }, { name: 'release', type: 'string' }, { name: 'summaries', type: 'list', reducer: 'append' },
    { name: 'digest', type: 'string' }, { name: 'email', type: 'object' }],
  nodes: [N('start', 'start', 40, { label: s.start }, 200),
    N('each', 'foreach', 280, { label: s.each, items_field: 'releases', item_field: 'release', max_items: 20 }, 200),
    N('sum', 'llm', 560, { label: s.summarize, model: 'gpt-4o-mini', prompt: 'Summarize in one line: {{state.release | trim}}', output_field: 'summaries' }, 60),
    N('compose', 'llm', 560, { label: s.compose, model: 'gpt-4o-mini', prompt: 'Write a short digest from {{state.summaries | join("\\n")}}', output_field: 'digest' }, 340),
    N('mail', 'email', 840, { label: s.send, to: 'team@example.com', subject: 'Release digest', body: '{{state.digest}}', format: 'text', output_field: 'email' }, 340),
    N('end', 'end', 1100, { label: s.end }, 340)],
  edges: [{ id: 'a', source: 'start', target: 'each' }, { id: 'b', source: 'each', target: 'sum', label: 'each' }, { id: 'c', source: 'sum', target: 'each' },
    { id: 'd', source: 'each', target: 'compose', label: 'done' }, { id: 'e', source: 'compose', target: 'mail' }, { id: 'f', source: 'mail', target: 'end' }],
})

const refund = (s: typeof T.en) => ({
  name: s.refund,
  state: [{ name: 'order_id', type: 'string' }, { name: 'amount', type: 'string' }, { name: 'reply', type: 'string' }, { name: 'decision', type: 'string' }],
  nodes: [N('start', 'start', 40, { label: s.start }, 180),
    N('draft', 'llm', 280, { label: s.draft, model: 'gpt-4o-mini', prompt: 'Draft a refund reply for order {{state.order_id}}', output_field: 'reply' }, 180),
    N('ask', 'human', 540, { label: s.approve, prompt: s.approvePrompt, output_field: 'decision', deadline: { after: '1d', remind_every: '4h', on_timeout: 'reject' } }, 180),
    N('route', 'condition', 800, { label: s.approved, field: 'decision', default: 'rejected' }, 180),
    N('mail', 'email', 1060, { label: s.notify, to: 'customer@example.com', subject: 'Your refund', body: '{{state.reply}}', format: 'text' }, 80),
    N('end', 'end', 1060, { label: s.end }, 300)],
  edges: [{ id: 'a', source: 'start', target: 'draft' }, { id: 'b', source: 'draft', target: 'ask' }, { id: 'c', source: 'ask', target: 'route' },
    { id: 'd', source: 'route', target: 'mail', label: 'approved' }, { id: 'e', source: 'route', target: 'end', label: 'rejected' }, { id: 'f', source: 'mail', target: 'end' }],
})

const normalize = (s: typeof T.en) => ({
  name: s.normalize,
  state: [{ name: 'payload', type: 'object' }, { name: 'event', type: 'object' }],
  nodes: [N('start', 'start', 40, { label: s.start }, 160),
    N('clean', 'tool', 320, { label: s.clean, mode: 'code', code: CODE, output_field: 'event' }, 160),
    N('end', 'end', 600, { label: s.end }, 160)],
  edges: [{ id: 'a', source: 'start', target: 'clean' }, { id: 'b', source: 'clean', target: 'end' }],
})

const RELEASES = JSON.stringify({ releases: ['v2.4: streaming tokens in the trace', 'v2.5: For each loops with max_items', 'v2.6: Code mode in a Docker sandbox'] }, null, 2)
const PAYLOAD = JSON.stringify({ payload: { id: 'evt_1042', type: 'ORDER.PAID', amount_cents: 12950 } }, null, 2)

async function shot(page: Page, lang: Lang, name: string) {
  await page.mouse.move(2, 898); await page.waitForTimeout(450)
  await page.screenshot({ path: `../handbook/docs/${lang}/images/${name}.png` })
}
async function setInput(page: Page, json: string) {
  await page.locator('#run-tab').click()
  await page.locator('#run-input').click(); await page.keyboard.press('ControlOrMeta+a'); await page.keyboard.insertText(json)
}
async function run(page: Page, status = 'ok') {
  await page.locator('#run-btn').click()
  await expect(page.locator('#trace-summary')).toHaveAttribute('data-status', status, { timeout: 30_000 })
}
async function fit(page: Page) { await page.keyboard.press('Shift+1'); await page.waitForTimeout(500) }

for (const lang of ['en', 'vi'] as Lang[]) {
  test.describe(`handbook ${lang}`, () => {
    test.use({ locale: lang === 'en' ? 'en-US' : 'vi-VN' })

    test(`capture ${lang}`, async ({ page }) => {
      const s = T[lang]
      await page.addInitScript(([l]) => { localStorage.setItem('lang', l); localStorage.setItem('theme', 'light') }, [lang])
      await page.goto('/login'); await expect(page.locator('#auth-submit')).toBeVisible()
      const token = await signIn(page, 'admin@example.com', 'admin123')
      const H = { Authorization: `Bearer ${token}` }
      // Start from a clean list: the other language's run shares this database
      for (const w of (await (await page.request.get('/api/workflows', { headers: H })).json()).data)
        if (w.id !== 'example') await page.request.delete(`/api/workflows/${w.id}?force=true`, { headers: H })
      for (const k of (await (await page.request.get('/api/knowledge-bases', { headers: H })).json()).data)
        await page.request.delete(`/api/knowledge-bases/${k.id}`, { headers: H })
      const make = async (wf: object) => (await (await page.request.post('/api/workflows', { headers: H, data: wf })).json()).data.id as string
      const ids = { digest: await make(digest(s)), refund: await make(refund(s)), normalize: await make(normalize(s)) }

      // Hero: the seeded Customer Support graph, after a run
      await page.goto('/workflows/example'); await expect(page.locator('.react-flow__node').first()).toBeVisible(); await fit(page)
      await shot(page, lang, 'editor')
      await setInput(page, JSON.stringify({ message: lang === 'en' ? 'Where is order A100?' : 'Đơn A100 của tôi đang ở đâu?' }, null, 2))
      await run(page)
      await shot(page, lang, 'run-trace')
      await page.locator('.react-flow__node[data-id="classify"]').click(); await expect(page.locator('#trace-diff')).toBeVisible()
      await shot(page, lang, 'trace-detail')

      // For each + LLM + Send email (dry run)
      await page.goto(`/workflows/${ids.digest}`); await expect(page.locator('.react-flow__node')).toHaveCount(6); await fit(page)
      await setInput(page, RELEASES); await run(page)
      await shot(page, lang, 'loop-run')
      await page.locator('.react-flow__node[data-id="mail"]').click()
      await shot(page, lang, 'email-node')

      // Human approval: the run waits
      await page.goto(`/workflows/${ids.refund}`); await expect(page.locator('.react-flow__node')).toHaveCount(6); await fit(page)
      await setInput(page, JSON.stringify({ order_id: 'A100', amount: '$129.50', reply: '', decision: '' }, null, 2))
      await run(page, 'waiting'); await expect(page.locator('#human-question')).toBeVisible()
      await shot(page, lang, 'human-waiting')
      await page.locator('.react-flow__node[data-id="ask"]').click(); await page.locator('#human-deadline').scrollIntoViewIfNeeded()
      await shot(page, lang, 'human-deadline')

      // Approvals inbox with the waiting refund, then the workflow list with its link (TASK-0065)
      await page.goto('/approvals'); await expect(page.locator('[data-testid=inbox-row]').first()).toBeVisible()
      await shot(page, lang, 'approvals')
      await page.goto('/workflows'); await expect(page.locator('#pending-runs')).toBeVisible()
      await shot(page, lang, 'workflows')
      await page.locator('#new-wf').click(); await expect(page.locator('#template-gallery')).toBeVisible()
      await shot(page, lang, 'templates'); await page.keyboard.press('Escape')

      // Workflow tests (TASK-0069): the Leave request template comes with its test cases; Run all with the mock model,
      // the case editor, then a mistake in version 2 shows as a regression against version 1
      const leave = (await (await page.request.post('/api/templates/builtin-leave-request/use', { headers: H, data: { name: lang === 'en' ? 'Leave request' : 'Đơn nghỉ phép' } })).json()).data.id
      const runTests = async () => {
        await page.locator('#tests-tab').click(); await page.locator('#tests-mock').click(); await page.locator('#tests-run-all').click()
        await expect(page.locator('#tests-compare')).toBeVisible({ timeout: 60_000 })
      }
      await page.goto(`/workflows/${leave}`); await expect(page.locator('.react-flow__node')).toHaveCount(5); await fit(page)
      await runTests(); await expect(page.locator('#tests-summary')).toContainText(lang === 'en' ? '2 passed, 0 failed' : '2 đạt, 0 không đạt')
      await shot(page, lang, 'tests')
      await page.getByTestId('test-edit').click(); await expect(page.locator('#test-dialog')).toBeVisible()
      await shot(page, lang, 'test-case'); await page.keyboard.press('Escape')
      // Export to Python (TASK-0072): version 1 in the Code tab, with the Human node's code marked
      await page.locator('#code-tab').click(); await page.locator('.react-flow__node[data-id="manager"]').click()
      await expect(page.locator('.cm-node-mark').first()).toBeVisible()
      await shot(page, lang, 'code-tab')
      const v1 = (await (await page.request.get(`/api/workflows/${leave}`, { headers: H })).json()).data
      v1.nodes.find((n: { id: string }) => n.id === 'manager').data.output_field = 'details'  // the answer now overwrites the details
      await page.request.post('/api/workflows', { headers: H, data: v1 })
      await page.reload(); await expect(page.locator('.react-flow__node')).toHaveCount(5); await fit(page)
      await runTests(); await expect(page.getByTestId('compare-regression')).toBeVisible()
      await shot(page, lang, 'tests-compare')
      await page.goto('/workflows'); await expect(page.locator('#new-wf')).toBeVisible()
      await page.locator('#creds-btn').click(); await page.waitForTimeout(400)
      await shot(page, lang, 'credentials'); await page.keyboard.press('Escape')

      // Editor dialogs on the digest workflow
      await page.goto(`/workflows/${ids.digest}`); await expect(page.locator('.react-flow__node')).toHaveCount(6)
      await page.locator('#more-btn').click(); await page.locator('#api-btn').click(); await page.waitForTimeout(500)
      await shot(page, lang, 'api-trigger'); await page.keyboard.press('Escape')
      await page.locator('#more-btn').click(); await page.locator('#schedules-btn').click(); await expect(page.locator('#schedules-dialog')).toBeVisible()
      await page.locator('#schedule-name').fill(s.morning); await page.locator('#schedule-cron').fill('0 8 * * 1-5')
      await expect(page.locator('#schedule-preview')).toBeVisible()
      await shot(page, lang, 'schedules'); await page.keyboard.press('Escape')
      await page.keyboard.press('ControlOrMeta+k'); await page.keyboard.insertText(lang === 'en' ? 'add' : 'thêm'); await page.waitForTimeout(400)
      await shot(page, lang, 'palette'); await page.keyboard.press('Escape')

      // Versions: rename a node, save, diff v1 and v2
      await page.locator('.react-flow__node[data-id="compose"]').click()
      const label = page.locator('div.space-y-1\\.5', { has: page.getByText(lang === 'en' ? 'Label' : 'Nhãn', { exact: true }) }).locator('input').first()
      {
        await label.fill(`${s.compose} (v2)`); await page.locator('#save-btn').click(); await expect(page.locator('#unsaved-badge')).toHaveCount(0)
        await page.locator('#more-btn').click(); await page.locator('#versions-btn').click()
        await expect(page.locator('[data-testid=version-row]').first()).toBeVisible(); await page.waitForTimeout(500)
        await shot(page, lang, 'versions'); await page.keyboard.press('Escape')
      }

      // Code mode
      const rt = (await (await page.request.get('/api/meta/runtime', { headers: H })).json()).data
      if (rt.available) {
        await page.goto(`/workflows/${ids.normalize}`); await expect(page.locator('.react-flow__node')).toHaveCount(3); await fit(page)
        await setInput(page, PAYLOAD)
        await page.locator('.react-flow__node[data-id="clean"]').click()
        await page.locator('#code-test').click()
        await expect(page.locator('#code-test-result')).toContainText('order.paid', { timeout: 60_000 })
        await page.locator('#code-test-result').scrollIntoViewIfNeeded()
        await shot(page, lang, 'code-node')
      }

      // Validation errors: a loop with no Condition and an unreachable node
      const broken = { name: s.broken, state: [{ name: 'message', type: 'string' }],
        nodes: [N('start', 'start', 40, { label: s.start }, 160),
          N('draft', 'llm', 280, { label: s.draft, model: 'gpt-4o-mini', prompt: '{{state.message}}', output_field: 'message' }, 80),
          N('refine', 'llm', 540, { label: s.refine, model: 'gpt-4o-mini', prompt: '{{state.missing}}', output_field: 'message' }, 80),
          N('lonely', 'tool', 280, { label: s.lonely, mode: 'function', function: 'lookup_order', output_field: 'message' }, 300),
          N('end', 'end', 800, { label: s.end }, 160)],
        edges: [{ id: '1', source: 'start', target: 'draft' }, { id: '2', source: 'draft', target: 'refine' }, { id: '3', source: 'refine', target: 'draft' },
          { id: '4', source: 'lonely', target: 'end' }] }
      await page.goto(`/workflows/${await make(broken)}`); await expect(page.locator('.react-flow__node')).toHaveCount(5); await fit(page)
      await page.locator('#run-btn').click(); await page.locator('#run-tab').click()
      await expect(page.locator('#validation-errors')).toBeVisible()
      await shot(page, lang, 'validation')

      // Settings, with one knowledge base so the page is not empty
      const kb = (await (await page.request.post('/api/knowledge-bases', { headers: H, data: { name: s.kb, description: s.kbDesc } })).json()).data
      await page.request.post(`/api/knowledge-bases/${kb.id}/documents`, { headers: H, multipart: { file: { name: 'shipping-faq.md', mimeType: 'text/markdown', buffer: Buffer.from(s.faq) } } })
      for (const sec of ['users', 'knowledge', 'mcp', 'channels', 'profile']) {
        await page.goto(`/settings/${sec}`); await page.waitForLoadState('networkidle'); await page.waitForTimeout(400)
        await shot(page, lang, `settings-${sec}`)
      }

      // Chat triggers (TASK-0077): a Slack connection (the fake API) and one trigger on the Leave request, opened for editing.
      // Made after the Channels shot so that one stays empty.
      const team = `T${lang.toUpperCase()}${Date.now().toString(36).toUpperCase()}`
      const ch = (await (await page.request.post('/api/approvals/channels', { headers: H, data: { kind: 'slack', name: 'Acme Slack', bot_token: `xoxb-1-${team}-abcdefgh`, signing_secret: '0123456789abcdef0123456789abcdef' } })).json()).data
      await page.request.post(`/api/workflows/${leave}/chat-triggers`, { headers: H, data: { name: lang === 'en' ? 'Leave requests' : 'Đơn nghỉ phép', channel_id: ch.id, place: 'C0HRLEAVE',
        command: lang === 'en' ? 'leave' : 'nghiphep', input_field: 'message', reply_field: 'decision', enabled: true } })
      await page.goto(`/workflows/${leave}`); await expect(page.locator('.react-flow__node')).toHaveCount(5)
      await page.locator('#more-btn').click(); await page.locator('#chat-triggers-btn').click(); await expect(page.locator('#chat-triggers-dialog')).toBeVisible()
      await page.locator('[data-testid=chat-trigger-row]').getByRole('button', { name: /^(Edit|Sửa) chat trigger/ }).click()
      await expect(page.locator('#chat-trigger-sample')).toBeVisible()
      await shot(page, lang, 'chat-triggers'); await page.keyboard.press('Escape')

      // Dark theme hero
      await page.evaluate(() => localStorage.setItem('theme', 'dark'))
      await page.addInitScript(() => localStorage.setItem('theme', 'dark'))
      await page.goto(`/workflows/${ids.digest}`); await expect(page.locator('.react-flow__node')).toHaveCount(6); await fit(page)
      await setInput(page, RELEASES); await run(page)
      await shot(page, lang, 'editor-dark')
    })
  })
}
