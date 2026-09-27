import { resolve } from 'node:path'
import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vite'

// Ein einziges ES-Modul ohne externe Abhängigkeiten (Vue, Kern und Stile gebündelt),
// ausgeliefert als Paketdaten von auditcore_runner (`runner-elements.js`).
export default defineConfig({
  plugins: [vue({ features: { customElement: false } })],
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
