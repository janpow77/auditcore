import { fileURLToPath } from 'node:url'
import { defineConfig } from 'vitest/config'

// Node ohne DOM: Der Kern darf weder `document` noch `window` brauchen.
export default defineConfig({
  resolve: {
    alias: [
      { find: /^@auditcore\/common\/browser$/, replacement: fileURLToPath(new URL('../common/src/browser.ts', import.meta.url)) },
      { find: /^@auditcore\/common$/, replacement: fileURLToPath(new URL('../common/src/index.ts', import.meta.url)) },
    ],
  },
  test: { environment: 'node', include: ['test/**/*.spec.ts'] },
})
