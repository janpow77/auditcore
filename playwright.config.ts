import { defineConfig, devices } from '@playwright/test'

// Bildparität Vue ↔ React der Basiskomponenten (packages-js/ui-react/visual).
// Baselines liegen im Repository und entstehen im Runner-Image (feste Browser und
// Schriften): `auditcore-runner lokal --profil gui` bzw. `npx playwright test --update-snapshots`
// im selben Image. Beide Fassungen vergleichen gegen dieselbe Datei.
export default defineConfig({
  testDir: 'packages-js/ui-react/visual',
  testMatch: '*.visual.ts',
  outputDir: '.auditcore-runner/playwright',
  snapshotPathTemplate: 'packages-js/ui-react/visual/baselines/{arg}{ext}',
  reporter: 'list',
  expect: { toHaveScreenshot: { maxDiffPixels: 0, animations: 'disabled', caret: 'hide' } },
  use: { baseURL: 'http://127.0.0.1:5197', viewport: { width: 480, height: 240 }, deviceScaleFactor: 1, locale: 'de-DE', timezoneId: 'UTC' },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'], viewport: { width: 480, height: 240 }, deviceScaleFactor: 1 } }],
  webServer: {
    command: 'npx vite --config packages-js/ui-react/visual/vite.config.ts --host 127.0.0.1 --port 5197 --strictPort',
    url: 'http://127.0.0.1:5197',
    reuseExistingServer: !process.env.CI,
    timeout: 60_000,
  },
})
