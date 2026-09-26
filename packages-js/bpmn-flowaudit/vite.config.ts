import { resolve } from 'node:path'
import { defineConfig } from 'vite'
import dts from 'vite-plugin-dts'

export default defineConfig({
  plugins: [dts({ include: ['src'], entryRoot: 'src' })],
  build: {
    lib: {
      entry: {
        index: resolve(import.meta.dirname, 'src/index.ts'),
        profiles: resolve(import.meta.dirname, 'src/profile/bundled.ts'),
        ui: resolve(import.meta.dirname, 'src/ui/index.ts'),
      },
      formats: ['es'],
    },
    rolldownOptions: {
      external: [/^bpmn-moddle/, /^diagram-js/, /^@auditcore\/bpmn-editor/],
    },
    sourcemap: true,
  },
})
