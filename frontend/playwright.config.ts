import { defineConfig } from '@playwright/test'
import os from 'os'
import path from 'path'

// Isolated stack: backend on 8100 (temp DB), Vite on 5190 proxying to it.
const API = 8100, UI = 5190
const db = path.join(os.tmpdir(), `lgs-e2e-${Date.now()}.db`)
export default defineConfig({
  testDir: './e2e',
  timeout: 60_000,
  workers: 1,
  reporter: [['list']],
  use: {
    baseURL: `http://127.0.0.1:${UI}`,
    headless: true,
    trace: 'retain-on-failure',
    // Use a system Chrome when PW_CHROME is set (no browser download needed); otherwise Playwright's Chromium.
    launchOptions: process.env.PW_CHROME ? { executablePath: process.env.PW_CHROME } : {},
  },
  webServer: [
    {
      command: `${process.env.E2E_UVICORN || '.venv/bin/uvicorn'} app.main:app --host 127.0.0.1 --port ${API}`,
      cwd: '../backend', url: `http://127.0.0.1:${API}/api/health`, reuseExistingServer: false, timeout: 60_000,
      env: { STUDIO_DB: db, STUDIO_IMPORT_DIR: path.join(os.tmpdir(), 'lgs-e2e-imports'), OPENAI_API_KEY: '' },
    },
    {
      command: `npx vite --host 127.0.0.1 --port ${UI} --strictPort`,
      url: `http://127.0.0.1:${UI}`, reuseExistingServer: false, timeout: 60_000,
      env: { STUDIO_API_PORT: String(API), STUDIO_UI_PORT: String(UI) },
    },
  ],
})
