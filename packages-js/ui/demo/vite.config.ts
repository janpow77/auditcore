import { fileURLToPath } from 'node:url'
import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vite'

const source = (path: string): string => fileURLToPath(new URL(`../src/${path}`, import.meta.url))

// Demo-App: nutzt die Quellen direkt, damit Änderungen sofort sichtbar sind.
export default defineConfig({
  root: fileURLToPath(new URL('.', import.meta.url)),
  base: './',
  plugins: [vue({ template: { compilerOptions: { isCustomElement: (tag) => tag.startsWith('flowaudit-') } } })],
  resolve: {
    alias: [
      { find: /^@flowaudit\/ui\/elements$/, replacement: source('elements.ts') },
      { find: /^@flowaudit\/ui$/, replacement: source('index.ts') },
      { find: /^@flowaudit\/kanban-core$/, replacement: fileURLToPath(new URL('../../kanban-core/src/index.ts', import.meta.url)) },
    ],
  },
  build: { outDir: 'dist', emptyOutDir: true },
  server: { port: 5190, strictPort: false },
  preview: { port: 5191 },
})
