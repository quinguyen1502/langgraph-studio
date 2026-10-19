import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

export const promoDir = path.dirname(fileURLToPath(import.meta.url))
export const repoRoot = path.resolve(promoDir, '../..')
export const buildDir = path.join(promoDir, 'build')
/** Where the video of one language goes: next to that site's pages. */
export const videoDir = lang => path.join(repoRoot, `handbook/docs/${lang}/assets/video`)
export const framesDir = lang => path.join(buildDir, 'frames', lang)

const candidates = [
  process.env.CHROME_PATH,
  '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  '/usr/bin/google-chrome',
  '/usr/bin/chromium',
  'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
]

/** An installed Chrome, or undefined to use Playwright's own Chromium. */
export function chromePath() {
  return candidates.find(p => p && fs.existsSync(p))
}
