import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'
import { sourceAliases } from './aliases.ts'

export default defineConfig({
  plugins: [vue()],
  resolve: { alias: sourceAliases() },
  test: {
    environment: 'happy-dom',
    include: ['test/**/*.spec.ts'],
    setupFiles: ['../bpmn-flowaudit/test/setup/svgTransforms.ts'],
  },
})
