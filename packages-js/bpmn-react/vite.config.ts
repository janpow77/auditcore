import { resolve } from 'node:path'
import { defineConfig } from 'vite'
import dts from 'vite-plugin-dts'

export default defineConfig({
  plugins: [dts({ include: ['src', '../bpmn-flowaudit/src/types'], entryRoot: 'src', tsconfigPath: './tsconfig.json', pathsToAliases: false, aliasesExclude: [/^@flowaudit\//] })],
  build: {
    lib: {
      entry: { index: resolve(__dirname, 'src/index.ts'), FlowauditBpmnEditor: resolve(__dirname, 'src/FlowauditBpmnEditor.ts') },
      formats: ['es'],
    },
    rollupOptions: { external: [/^react($|\/)/, /^react-dom($|\/)/, /^@flowaudit\//] },
    sourcemap: true,
  },
})
