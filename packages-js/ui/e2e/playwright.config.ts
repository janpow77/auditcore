import { defineConfig, devices } from '@playwright/test'

// Prüft die gebaute Demo-App (npm run demo:build) über vite preview.
export default defineConfig({
  testDir: '.',
  testMatch: '*.e2e.ts',
  outputDir: '../test-results',
  reporter: 'list',
  use: { baseURL: 'http://127.0.0.1:5191', trace: 'retain-on-failure' },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
  webServer: {
    command: 'npx vite preview --config demo/vite.config.ts --host 127.0.0.1 --port 5191 --strictPort',
    cwd: '..',
    url: 'http://127.0.0.1:5191',
    reuseExistingServer: !process.env.CI,
    timeout: 60_000,
  },
})
