import { fileURLToPath } from 'node:url'
import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vitest/config'

const ui = (path: string): string => fileURLToPath(new URL(`../ui/src/${path}`, import.meta.url))

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: [
      { find: /^@flowaudit\/ui\/elements$/, replacement: ui('elements.ts') },
      { find: /^@flowaudit\/ui$/, replacement: ui('index.ts') },
    ],
  },
  test: {
    environment: 'happy-dom',
    include: ['test/**/*.spec.ts', 'test/**/*.spec.tsx'],
  },
})
