import { resolve } from 'node:path'
import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vite'

const js = (name: string, entry = 'src/index.ts') => resolve(import.meta.dirname, '..', '..', name, entry)

// Ein einziges ES-Modul ohne externe Abhängigkeiten (Vue, Kern und Stile gebündelt),
// ausgeliefert als Paketdaten von auditcore_runner (`runner-elements.js`). Die
// Workspace-Pakete werden aus den Quellen gebaut, nie aus einem vorhandenen
// dist/ – sonst hinge das Ergebnis vom lokalen Baustand ab.
export default defineConfig({
  plugins: [vue({ features: { customElement: false } })],
  resolve: {
    alias: [
      { find: /^@auditcore\/ui-core\/style\.css/, replacement: js('ui-core', 'styles/index.css') },
      { find: /^@auditcore\/ui-core$/, replacement: js('ui-core') },
      { find: /^@auditcore\/common$/, replacement: js('common') },
      { find: /^@auditcore\/kanban-core$/, replacement: js('kanban-core') },
    ],
  },
  define: { 'process.env.NODE_ENV': JSON.stringify('production') },
  build: {
    outDir: resolve(import.meta.dirname, 'dist'),
    emptyOutDir: true,
    lib: {
      entry: resolve(import.meta.dirname, 'runner-elements.ts'),
      formats: ['es'],
      fileName: () => 'runner-elements.js',
    },
    minify: true,
    sourcemap: false,
  },
})
