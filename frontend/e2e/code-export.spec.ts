import { test, expect } from '@playwright/test'
import { readFile } from 'node:fs/promises'
import { login, newWorkflow, SIMPLE } from './helpers'
// TASK-0071 (REQ-0043): the Code tab shows the saved workflow as LangGraph code, follows the node selected on the
// canvas, copies and downloads the file, reloads after a save; imported repositories have no Code tab.

test('Code tab: Python of the saved version, the selected node highlighted, copy and download', async ({ page, context }) => {
  await context.grantPermissions(['clipboard-read', 'clipboard-write'])
  const H = await login(page)
  const wid = await newWorkflow(page, H, SIMPLE(`Python e2e ${Date.now()}`))
  await page.goto(`/workflows/${wid}`)

  // the ⋯ menu opens it, like the command palette
  await page.locator('#more-btn').click(); await page.locator('#code-btn').click()
  const code = page.locator('#code-view')
  await expect(code).toContainText('a LangGraph graph exported from Superstep')  // CodeMirror renders the lines in view
  await expect(page.locator('#code-file')).toHaveText(/^python_e2e_\d+\.py$/)
  await expect(page.locator('#code-export-language')).toHaveText('Python')
  await expect(page.locator('#code-version')).toHaveText('v1')
  await expect(page.locator('#code-hint')).toContainText('Chọn một node')

  // selecting a node marks its function
  await page.locator('.react-flow__node[data-id="reply"]').click()
  await expect(page.locator('#code-hint')).toContainText('“Reply”')
  await expect(page.locator('.cm-node-mark').first()).toContainText('REPLY_PROMPT')
  await expect(page.locator('.cm-node-mark').filter({ hasText: 'def reply(state: State) -> dict:' })).toHaveCount(1)

  await page.locator('#code-copy').click()
  expect(await page.evaluate(() => navigator.clipboard.readText())).toContain('def build_graph(checkpointer=None):')
  const dl = page.waitForEvent('download'); await page.locator('#code-download').click()
  const file = await dl
  expect(file.suggestedFilename()).toMatch(/^python_e2e_\d+\.py$/)
  expect(await readFile((await file.path())!, 'utf8')).toContain('if __name__ == "__main__":')

  // a change shows as unsaved until it is saved; then the code is the new version's
  await page.locator('#llm-prompt').click(); await page.keyboard.press('ControlOrMeta+a'); await page.keyboard.insertText('Answer briefly: {{state.message}}')
  await expect(page.locator('#code-unsaved')).toBeVisible()
  await page.locator('#save-btn').click()
  await expect(page.locator('#code-version')).toHaveText('v2')
  await expect(code).toContainText('Answer briefly: {{state.message}}')
  await expect(page.locator('#code-unsaved')).toHaveCount(0)
})

test('Code tab: none for an imported repository', async ({ page }) => {
  const H = await login(page)
  const wid = await newWorkflow(page, H, SIMPLE(`Python import e2e ${Date.now()}`))
  // only an import sets `source`; the API refuses it from clients, so the page is shown one
  await page.route(`**/api/workflows/${wid}`, async r => {
    const res = await r.fetch(); const body = await res.json()
    body.data.source = { kind: 'langgraph_import', repo_url: 'https://github.com/example/agent', ref: 'main' }
    await r.fulfill({ response: res, json: body })
  })
  await page.goto(`/workflows/${wid}`)
  await expect(page.locator('#tests-tab')).toHaveCount(0)
  await expect(page.locator('#code-tab')).toHaveCount(0)
  await page.locator('#more-btn').click()
  await expect(page.locator('#code-btn')).toHaveAttribute('data-disabled', '')
})

test('Code tab: TypeScript (LangGraph.js) export, remembered, highlighted and downloaded as .ts', async ({ page }) => {
  // TASK-0082 (REQ-0047): the language picker asks the same exporter API for LangGraph.js TypeScript
  const H = await login(page)
  const wid = await newWorkflow(page, H, SIMPLE(`TS export e2e ${Date.now()}`))
  await page.goto(`/workflows/${wid}`)
  await page.locator('#more-btn').click(); await page.locator('#code-btn').click()
  await page.locator('#code-export-language').click(); await page.locator('#code-export-language-typescript').click()
  const code = page.locator('#code-view')
  await expect(code).toContainText('a LangGraph.js graph exported from Superstep')
  await expect(page.locator('#code-file')).toHaveText(/^ts_export_e2e_\d+\.ts$/)
  await expect(page.locator('#code-view')).toHaveAttribute('data-language', 'typescript')
  await expect(page.locator('#code-download')).toHaveText('Tải .ts')

  await page.locator('.react-flow__node[data-id="reply"]').click()
  await expect(page.locator('.cm-node-mark').filter({ hasText: 'async function reply(state: State): Promise<Update> {' })).toHaveCount(1)
  const dl = page.waitForEvent('download'); await page.locator('#code-download').click()
  expect((await dl).suggestedFilename()).toMatch(/^ts_export_e2e_\d+\.ts$/)

  await page.reload()  // the choice is remembered in this browser
  await page.locator('#more-btn').click(); await page.locator('#code-btn').click()
  await expect(page.locator('#code-export-language')).toHaveText('TypeScript')
  await expect(code).toContainText('a LangGraph.js graph exported from Superstep')
})
