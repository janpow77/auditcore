import { resolve } from 'node:path'
import { defineConfig } from 'vite'
import dts from 'vite-plugin-dts'

// Zwei Einstiege: Kern ohne DOM (index) und der getrennt ladbare Excel-Austausch (xlsx, mit fflate).
export default defineConfig({
  plugins: [dts({ include: ['src'], tsconfigPath: './tsconfig.json', entryRoot: 'src', pathsToAliases: false })],
  build: {
    lib: {
      entry: { index: resolve(import.meta.dirname, 'src/index.ts'), xlsx: resolve(import.meta.dirname, 'src/xlsx/index.ts') },
      formats: ['es'],
    },
    rolldownOptions: { external: [/^@auditcore\/common(\/.*)?$/, 'fflate'] },
    sourcemap: true,
  },
})
