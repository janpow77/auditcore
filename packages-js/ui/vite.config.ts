import { resolve } from 'node:path'
import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vite'
import dts from 'vite-plugin-dts'

// Bibliotheksbau: Vue-Komponenten (index) und Web Components (elements) als ES-Module.
export default defineConfig({
  plugins: [vue(), dts({ include: ['src'], tsconfigPath: './tsconfig.json', entryRoot: 'src', pathsToAliases: false })],
  build: {
    lib: {
      entry: {
        index: resolve(import.meta.dirname, 'src/index.ts'),
        elements: resolve(import.meta.dirname, 'src/elements.ts'),
      },
      formats: ['es'],
      cssFileName: 'ui',
    },
    rolldownOptions: {
      // Stile des Kerns (@flowaudit/ui-core/style.css) werden in ui.css gebündelt, nur der JS-Einstieg bleibt extern.
      external: ['vue', '@flowaudit/kanban-core', '@flowaudit/ui-core', /^@flowaudit\/common(\/.*)?$/, 'leaflet'],
    },
    sourcemap: true,
  },
})
