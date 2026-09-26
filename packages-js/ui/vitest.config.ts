import { fileURLToPath } from 'node:url'
import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vitest/config'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: [
      { find: /^@auditcore\/ui-core\/style\.css$/, replacement: fileURLToPath(new URL('../ui-core/styles/index.css', import.meta.url)) },
      { find: /^@auditcore\/ui-core$/, replacement: fileURLToPath(new URL('../ui-core/src/index.ts', import.meta.url)) },
      { find: /^@auditcore\/kanban-core$/, replacement: fileURLToPath(new URL('../kanban-core/src/index.ts', import.meta.url)) },
      { find: /^@auditcore\/common\/browser$/, replacement: fileURLToPath(new URL('../common/src/browser.ts', import.meta.url)) },
      { find: /^@auditcore\/common$/, replacement: fileURLToPath(new URL('../common/src/index.ts', import.meta.url)) },
    ],
  },
  test: {
    environment: 'happy-dom',
    include: ['test/**/*.spec.ts', 'src/**/*.spec.ts'],
  },
})
