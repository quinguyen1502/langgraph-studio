import { test, expect, type Page } from '@playwright/test'
import { login, newWorkflow, N } from './helpers'
import { expectRowAligned, expectBaselineAligned } from './helpers/alignment'

/** Alignment guardrails (docs/ui-conventions.md, rule 11): the main toolbars and rows share control heights,
 * vertical centres and text baselines, in light and dark, English and Vietnamese. */
const WF = { name: 'Align check', state: [{ name: 'message', type: 'string' }, { name: 'reply', type: 'string' }, { name: 'decision', type: 'string' }],
  nodes: [N('start', 'start', 40), N('bot', 'llm', 300, { label: 'Answer', model: 'gpt-4o-mini', prompt: 'Reply to {{state.message}}', output_field: 'reply' }),
    N('ask', 'human', 560, { label: 'Approve', prompt: 'OK?', output_field: 'decision' }), N('end', 'end', 820)],
  edges: [{ id: '1', source: 'start', target: 'bot' }, { id: '2', source: 'bot', target: 'ask' }, { id: '3', source: 'ask', target: 'end' }] }

const visible = async (page: Page, sel: string) => { const l = page.locator(sel); const n = await l.count(); const out = []
  for (let i = 0; i < n; i++) if (await l.nth(i).isVisible()) out.push(l.nth(i)); return out }

for (const [lang, theme] of [['en', 'light'], ['vi', 'light'], ['en', 'dark'], ['vi', 'dark']] as const) {
  test(`rows are aligned (${theme}, ${lang})`, async ({ page }) => {
    test.setTimeout(90_000)
    await page.setViewportSize({ width: 1600, height: 960 })
    const H = await login(page)
    await page.evaluate(([l, t]) => { localStorage.setItem('lang', l); localStorage.setItem('theme', t) }, [lang, theme])

    // workflow list toolbar: search, credentials, import, new (same height); the show-all switch and its label (same centre)
    await page.goto('/workflows'); await expect(page.locator('#new-wf')).toBeVisible()
    const toolbar = await visible(page, '#wf-search, #creds-btn, #import-btn, #new-wf')
    await expectRowAligned(toolbar, { label: 'workflow list toolbar' })
    if (await page.locator('#wf-all').isVisible()) await expectRowAligned([page.locator('#wf-search'), page.locator('#wf-all'), page.locator('label[for=wf-all]')], { sameHeight: false, label: 'show-all switch' })
    await expectRowAligned(await visible(page, 'header :is(button, a[data-slot=button])'), { label: 'list header' })

    // dialog footers: rename (Dialog) and delete (AlertDialog)
    const wid = await newWorkflow(page, H, WF); await page.reload()
    const row = page.locator('tr', { hasText: 'Align check' }).first()
    await row.locator('.wf-actions').click(); await page.getByRole('menuitem').nth(0).click(); await expect(page.locator('#rename-input')).toBeVisible()
    await expectRowAligned(await visible(page, '[data-slot=dialog-footer] button'), { label: 'rename dialog footer' })
    await expectBaselineAligned(await visible(page, '[data-slot=dialog-footer] button'), { label: 'rename dialog footer' })
    await page.keyboard.press('Escape'); await expect(page.locator('#rename-input')).toBeHidden()
    await row.locator('.wf-actions').click(); await page.getByRole('menuitem').nth(2).click(); await expect(page.locator('[data-slot=alert-dialog-footer]')).toBeVisible()
    await expectRowAligned(await visible(page, '[data-slot=alert-dialog-footer] button'), { label: 'delete dialog footer' })
    await page.keyboard.press('Escape')

    // editor header: every control in the top bar
    await page.goto(`/workflows/${wid}`); await expect(page.locator('#run-btn')).toBeVisible()
    await expectRowAligned(await visible(page, 'header :is(button, input, a[data-slot=button])'), { label: 'editor header' })
    await expectBaselineAligned([page.locator('#save-btn'), page.locator('#run-btn'), page.locator('#step-btn')], { label: 'editor header buttons' })

    // run panel: tab row, then the trace summary row after a run
    await expectRowAligned(await visible(page, '[role=tablist] >> nth=0 >> [role=tab]'), { label: 'run panel tabs' })
    await page.locator('#run-input').fill('{"message": "hi"}')
    await page.locator('#run-btn').click(); await expect(page.locator('#trace-summary')).toHaveAttribute('data-status', /ok|waiting/, { timeout: 30_000 })
    await page.locator('#run-btn').hover(); await page.mouse.move(0, 0)
    const summary = await visible(page, '#trace-summary > span')
    await expectRowAligned(summary, { sameHeight: false, label: 'trace summary' })
    await expectBaselineAligned(summary, { label: 'trace summary' })
    await expectRowAligned([summary[0], ...await visible(page, '#trace-summary :is(button, [role=switch])')], { sameHeight: false, tolerance: 1, label: 'trace summary controls' })

    // config panel: the LLM model field (input + load button) and the Human deadline switch row
    await page.locator('.react-flow__node[data-id="bot"]').click()
    const load = page.locator('[id$="-load"]').first(); await expect(load).toBeVisible()
    const inputId = (await load.getAttribute('id'))!.replace(/-load$/, '')
    await expectRowAligned([page.locator(`[id="${inputId}"]`), load], { label: 'model field' })
    await page.locator('.react-flow__node[data-id="ask"]').click(); await expect(page.locator('#deadline-on')).toBeVisible()
    await expectRowAligned([page.locator('label[for=deadline-on]'), page.locator('#deadline-on')], { sameHeight: false, label: 'deadline switch row' })
    await page.locator('#deadline-on').click()
    await expectRowAligned(await visible(page, '#deadline-after, #deadline-after-unit'), { label: 'deadline duration field' })
  })
}
