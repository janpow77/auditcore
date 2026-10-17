/**
 * Browsertest der Demo (`npm run test:e2e`). Nicht Teil von `npm test`: Er braucht
 * einen Playwright-Browser (`npx playwright install chromium`). Geprüft wird der
 * gebaute Stand mit strenger Content-Security-Policy. Bildschirmfotos liegen in
 * `e2e-results/` (von git ausgeschlossen) oder im Verzeichnis `SAMPLING_SCREENSHOTS`.
 */
import { defineConfig } from '@playwright/test'

const URL = 'http://127.0.0.1:5196'

export default defineConfig({
  testDir: 'e2e',
  outputDir: 'e2e-results/artifacts',
  timeout: 60_000,
  workers: 1,
  reporter: 'list',
  use: { baseURL: URL, viewport: { width: 1280, height: 900 }, locale: 'de-DE', timezoneId: 'Europe/Berlin' },
  webServer: {
    command: 'npx vite build -c demo/vite.config.ts && npx vite preview -c demo/vite.config.ts --host 127.0.0.1 --port 5196 --strictPort',
    url: URL,
    reuseExistingServer: false,
    timeout: 120_000,
  },
})
