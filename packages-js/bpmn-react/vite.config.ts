import { resolve } from 'node:path'
import { defineConfig } from 'vite'
import dts from 'vite-plugin-dts'
import { isExternal, styleAlias } from './aliases.ts'

export default defineConfig({
  plugins: [dts({ include: ['src', '../bpmn-flowaudit/src/types/css.d.ts', '../bpmn-editor/src/types/shims.d.ts'], entryRoot: 'src', tsconfigPath: './tsconfig.json', pathsToAliases: false, aliasesExclude: [/^@auditcore\//] })],
  resolve: { alias: styleAlias },
  oxc: { jsx: { runtime: 'automatic' } },
  build: {
    lib: { entry: resolve(import.meta.dirname, 'src/index.ts'), formats: ['es'], fileName: 'index', cssFileName: 'bpmn-react' },
    rolldownOptions: { external: isExternal },
    sourcemap: true,
  },
})
