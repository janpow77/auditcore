import { fileURLToPath } from 'node:url'
import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vitest/config'

const sibling = (path: string): string => fileURLToPath(new URL(`../${path}`, import.meta.url))

// Tests laufen gegen die Quellen der Nachbarpakete, nicht gegen deren (noch nicht gebautes) dist.
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: [
      { find: /^@auditcore\/ui-core\/style\.css$/, replacement: sibling('ui-core/styles/index.css') },
      { find: /^@auditcore\/ui-core$/, replacement: sibling('ui-core/src/index.ts') },
      { find: /^@auditcore\/ui\/elements$/, replacement: sibling('ui/src/elements.ts') },
      { find: /^@auditcore\/ui$/, replacement: sibling('ui/src/index.ts') },
      { find: /^@auditcore\/kanban-core$/, replacement: sibling('kanban-core/src/index.ts') },
      { find: /^@auditcore\/common\/browser$/, replacement: sibling('common/src/browser.ts') },
      { find: /^@auditcore\/common$/, replacement: sibling('common/src/index.ts') },
    ],
  },
  test: { environment: 'happy-dom', include: ['test/**/*.spec.ts'] },
})
