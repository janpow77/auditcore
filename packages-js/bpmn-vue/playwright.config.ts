/**
 * Browser test of the demo app (`npm run test:e2e`). Not part of `npm test`:
 * it needs a Playwright browser (`npx playwright install chromium`).
 * Screenshots land in `e2e-results/` (ignored by git).
 */

import { defineConfig } from '@playwright/test'

export default defineConfig({
  testDir: 'e2e',
  outputDir: 'e2e-results/artifacts',
  timeout: 60_000,
  use: { baseURL: 'http://127.0.0.1:5199', viewport: { width: 1600, height: 950 }, locale: 'de-DE' },
  webServer: { command: 'npx vite -c demo/vite.config.ts --host 127.0.0.1 --port 5199 --strictPort', url: 'http://127.0.0.1:5199', reuseExistingServer: true, timeout: 60_000 },
})
