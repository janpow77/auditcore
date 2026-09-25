import { fileURLToPath } from 'node:url'
import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vitest/config'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: [{ find: /^@flowaudit\/kanban-core$/, replacement: fileURLToPath(new URL('../kanban-core/src/index.ts', import.meta.url)) }],
  },
  test: {
    environment: 'happy-dom',
    include: ['test/**/*.spec.ts', 'src/**/*.spec.ts'],
  },
})
