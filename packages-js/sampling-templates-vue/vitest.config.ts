import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vitest/config'
import { sourceAliases } from './aliases.ts'

export default defineConfig({
  plugins: [vue()],
  resolve: { alias: sourceAliases },
  test: { environment: 'happy-dom', include: ['test/**/*.spec.ts'] },
})
