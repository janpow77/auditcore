import { defineConfig, devices } from '@playwright/test'

// Browserprüfung der Fachkomponenten mit REST-Port (Stichprobe, Benford):
// gebaute Demo über vite preview plus Demo-Backend demo/api_server.py.
// Python mit auditcore_sampling[web], auditcore_statistics[web] und uvicorn
// über FA_DEMO_PYTHON wählen (Standard: python3).
const python = process.env.FA_DEMO_PYTHON ?? 'python3'
// Eigene Ports, damit nie ein fremder Server wiederverwendet wird.
const apiPort = process.env.FA_DEMO_API_PORT ?? '18765'
const previewPort = process.env.FA_DEMO_PREVIEW_PORT ?? '5291'

export default defineConfig({
  testDir: '.',
  testMatch: '*.api-e2e.ts',
  outputDir: '../test-results',
  reporter: 'list',
  use: { baseURL: `http://127.0.0.1:${previewPort}`, trace: 'retain-on-failure' },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'], viewport: { width: 1360, height: 900 } } }],
  webServer: [
    {
      command: `${python} demo/api_server.py`,
      cwd: '..',
      url: `http://127.0.0.1:${apiPort}/api/sampling/profiles`,
      env: { FA_DEMO_API_PORT: apiPort },
      reuseExistingServer: false,
      timeout: 60_000,
    },
    {
      command: `npx vite preview --config demo/vite.config.ts --host 127.0.0.1 --port ${previewPort} --strictPort`,
      cwd: '..',
      url: `http://127.0.0.1:${previewPort}`,
      env: { FA_DEMO_API: `http://127.0.0.1:${apiPort}` },
      reuseExistingServer: false,
      timeout: 60_000,
    },
  ],
})
