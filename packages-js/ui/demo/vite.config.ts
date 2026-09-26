import { fileURLToPath } from 'node:url'
import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vite'

const api = process.env.FA_DEMO_API ?? 'http://127.0.0.1:18765'
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
      { find: /^@flowaudit\/common\/browser$/, replacement: fileURLToPath(new URL('../../common/src/browser.ts', import.meta.url)) },
      { find: /^@flowaudit\/common$/, replacement: fileURLToPath(new URL('../../common/src/index.ts', import.meta.url)) },
    ],
  },
  build: { outDir: 'dist', emptyOutDir: true },
  // Fachkomponenten mit REST-Port (Stichprobe, Benford): Demo-Backend demo/api_server.py.
  server: { port: 5190, strictPort: false, proxy: { '/api': api } },
  preview: { port: 5191, proxy: { '/api': api } },
})
