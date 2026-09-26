import { resolve } from 'node:path'
import { defineConfig } from 'vite'
import dts from 'vite-plugin-dts'
import { isExternal, styleAlias } from './aliases'

export default defineConfig({
  plugins: [dts({ include: ['src', '../bpmn-flowaudit/src/types/css.d.ts', '../bpmn-editor/src/types/shims.d.ts'], entryRoot: 'src', tsconfigPath: './tsconfig.json', pathsToAliases: false, aliasesExclude: [/^@flowaudit\//] })],
  resolve: { alias: styleAlias },
  esbuild: { jsx: 'automatic' },
  build: {
    lib: { entry: resolve(__dirname, 'src/index.ts'), formats: ['es'], fileName: 'index', cssFileName: 'bpmn-react' },
    rollupOptions: { external: isExternal },
    sourcemap: true,
  },
})
