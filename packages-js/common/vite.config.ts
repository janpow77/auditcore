import { resolve } from 'node:path'
import { defineConfig } from 'vite'
import dts from 'vite-plugin-dts'

// Zwei Einstiege: framework- und DOM-freier Kern (index) und Browser-Helfer (browser).
export default defineConfig({
  plugins: [dts({ include: ['src'], tsconfigPath: './tsconfig.json', entryRoot: 'src' })],
  build: {
    lib: {
      entry: { index: resolve(__dirname, 'src/index.ts'), browser: resolve(__dirname, 'src/browser.ts') },
      formats: ['es'],
    },
    sourcemap: true,
  },
})
