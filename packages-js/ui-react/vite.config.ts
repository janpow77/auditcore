import { resolve } from 'node:path'
import { defineConfig } from 'vite'
import dts from 'vite-plugin-dts'

export default defineConfig({
  plugins: [dts({ include: ['src'], tsconfigPath: './tsconfig.json', entryRoot: 'src', pathsToAliases: false })],
  build: {
    lib: { entry: { index: resolve(import.meta.dirname, 'src/index.ts') }, formats: ['es'] },
    rolldownOptions: {
      external: ['react', 'react-dom', 'react/jsx-runtime', 'vue', /^@flowaudit\/ui(-core)?(\/.*)?$/, '@flowaudit/kanban-core', /^@flowaudit\/common(\/.*)?$/],
    },
    sourcemap: true,
  },
})
