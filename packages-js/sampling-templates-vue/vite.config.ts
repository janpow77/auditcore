import { resolve } from 'node:path'
import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vite'
import dts from 'vite-plugin-dts'
import { isExternal, styleAlias } from './aliases.ts'

// Bibliotheksbau: Vue-Komponenten als ES-Modul; der Stil des Kerns steckt in sampling-templates-vue.css.
export default defineConfig({
  plugins: [vue(), dts({ include: ['src'], tsconfigPath: './tsconfig.json', entryRoot: 'src', pathsToAliases: false })],
  resolve: { alias: styleAlias },
  build: {
    lib: { entry: resolve(import.meta.dirname, 'src/index.ts'), formats: ['es'], fileName: 'index', cssFileName: 'sampling-templates-vue' },
    rolldownOptions: { external: isExternal },
    sourcemap: true,
  },
})
