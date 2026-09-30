import { resolve } from 'node:path'
import vue from '@vitejs/plugin-vue'
import dts from 'vite-plugin-dts'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [vue(), dts({ include: ['src'], tsconfigPath: './tsconfig.json', entryRoot: 'src', pathsToAliases: false })],
  build: {
    lib: { entry: { index: resolve(import.meta.dirname, 'src/index.ts'), elements: resolve(import.meta.dirname, 'src/elements.ts') }, formats: ['es'], cssFileName: 'layout' },
    rolldownOptions: { external: ['vue', '@auditcore/ui', '@auditcore/ui/elements'] },
    sourcemap: true,
  },
})
