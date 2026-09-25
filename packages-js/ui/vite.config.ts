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
        index: resolve(__dirname, 'src/index.ts'),
        elements: resolve(__dirname, 'src/elements.ts'),
      },
      formats: ['es'],
      cssFileName: 'ui',
    },
    rollupOptions: {
      external: ['vue', '@flowaudit/kanban-core', /^@flowaudit\/common(\/.*)?$/],
    },
    sourcemap: true,
  },
})
