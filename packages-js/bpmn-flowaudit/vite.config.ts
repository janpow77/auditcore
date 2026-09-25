import { resolve } from 'node:path'
import { defineConfig } from 'vite'
import dts from 'vite-plugin-dts'

export default defineConfig({
  plugins: [dts({ include: ['src'], entryRoot: 'src' })],
  build: {
    lib: {
      entry: {
        index: resolve(__dirname, 'src/index.ts'),
        profiles: resolve(__dirname, 'src/profile/bundled.ts'),
      },
      formats: ['es'],
    },
    rollupOptions: {
      external: [/^bpmn-moddle/, /^diagram-js/, /^@flowaudit\/bpmn-editor/],
    },
    sourcemap: true,
  },
})
