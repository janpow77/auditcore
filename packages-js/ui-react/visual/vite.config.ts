import { fileURLToPath } from 'node:url'
import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vite'

const pfad = (relativ: string): string => fileURLToPath(new URL(relativ, import.meta.url))

// Bühne der Bildparität (Playwright, playwright.config.ts im Repository-Wurzelverzeichnis).
export default defineConfig({
  root: pfad('.'),
  plugins: [vue()],
  resolve: {
    alias: [
      { find: /^@auditcore\/ui-core\/style\.css$/, replacement: pfad('../../ui-core/styles/index.css') },
      { find: /^@auditcore\/ui-core$/, replacement: pfad('../../ui-core/src/index.ts') },
      { find: /^@auditcore\/ui\/elements$/, replacement: pfad('../../ui/src/elements.ts') },
      { find: /^@auditcore\/ui$/, replacement: pfad('../../ui/src/index.ts') },
      { find: /^@auditcore\/kanban-core$/, replacement: pfad('../../kanban-core/src/index.ts') },
      { find: /^@auditcore\/common\/browser$/, replacement: pfad('../../common/src/browser.ts') },
      { find: /^@auditcore\/common$/, replacement: pfad('../../common/src/index.ts') },
    ],
  },
  build: { outDir: pfad('dist'), emptyOutDir: true },
})
