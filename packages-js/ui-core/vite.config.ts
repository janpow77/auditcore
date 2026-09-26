import { resolve } from 'node:path'
import { defineConfig } from 'vite'
import dts from 'vite-plugin-dts'

// Framework-freier Kern: nur ES-Modul und Typen; Stile liegen unverändert unter styles/.
export default defineConfig({
  plugins: [dts({ include: ['src'], tsconfigPath: './tsconfig.json', entryRoot: 'src', pathsToAliases: false })],
  build: {
    lib: { entry: resolve(__dirname, 'src/index.ts'), formats: ['es'], fileName: 'index' },
    rollupOptions: { external: [/^@flowaudit\/common(\/.*)?$/] },
    sourcemap: true,
  },
})
