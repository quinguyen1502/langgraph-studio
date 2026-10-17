import { defineConfig } from '@playwright/test'
import os from 'os'
import path from 'path'

// Isolated stack: backend on 8100 (temp DB), Vite on 5190 proxying to it.
const API = 8100, UI = 5190, CHAT = 8111  // CHAT: fake Slack/Telegram APIs (backend/tests/fixtures/mock_chat_api.py)
const db = path.join(os.tmpdir(), `lgs-e2e-${Date.now()}.db`)
export default defineConfig({
  testDir: './e2e',
  timeout: 60_000,
  workers: 1,
  reporter: [['list']],
  use: {
    locale: 'vi-VN', // existing specs assert Vietnamese UI text; i18n.spec.ts covers English + switching
    baseURL: `http://127.0.0.1:${UI}`,
    headless: true,
    trace: 'retain-on-failure',
    // Use a system Chrome when PW_CHROME is set (no browser download needed); otherwise Playwright's Chromium.
    launchOptions: process.env.PW_CHROME ? { executablePath: process.env.PW_CHROME } : {},
  },
  webServer: [
    { command: `python3 tests/fixtures/mock_chat_api.py ${CHAT}`, cwd: '../backend', url: `http://127.0.0.1:${CHAT}/health`, reuseExistingServer: false, timeout: 30_000 },
    {
      command: `${process.env.E2E_UVICORN || '.venv/bin/uvicorn'} app.main:app --host 127.0.0.1 --port ${API}`,
      cwd: '../backend', url: `http://127.0.0.1:${API}/api/health`, reuseExistingServer: false, timeout: 60_000,
      env: { STUDIO_DB: db, STUDIO_IMPORT_DIR: path.join(os.tmpdir(), 'lgs-e2e-imports'), OPENAI_API_KEY: '', STUDIO_ENABLE_DEMO_TOOLS: '1', STUDIO_RUN_TIMEOUT: '5', STUDIO_ALLOW_PRIVATE_CALLBACKS: '1', STUDIO_WEBHOOK_BACKOFF_BASE: '0.5', SLACK_API_URL: `http://127.0.0.1:${CHAT}/slack`, TELEGRAM_API_URL: `http://127.0.0.1:${CHAT}/telegram` },
    },
    {
      command: `npx vite --host 127.0.0.1 --port ${UI} --strictPort`,
      url: `http://127.0.0.1:${UI}`, reuseExistingServer: false, timeout: 60_000,
      env: { STUDIO_API_PORT: String(API), STUDIO_UI_PORT: String(UI) },
    },
  ],
})
