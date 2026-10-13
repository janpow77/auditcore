import { resolve } from 'node:path'
import { defineConfig } from 'vite'
import dts from 'vite-plugin-dts'

// Zwei Einstiege: Kern ohne DOM (index) und der getrennt ladbare Excel-Austausch (workbook, mit fflate).
// Der Einstieg heißt nicht „xlsx“: Bündelregeln einbindender Anwendungen ordnen Module mit diesem Namen oft SheetJS zu.
export default defineConfig({
  plugins: [dts({ include: ['src'], tsconfigPath: './tsconfig.json', entryRoot: 'src', pathsToAliases: false })],
  build: {
    lib: {
      entry: { index: resolve(import.meta.dirname, 'src/index.ts'), workbook: resolve(import.meta.dirname, 'src/xlsx/index.ts') },
      formats: ['es'],
    },
    rolldownOptions: { external: [/^@auditcore\/common(\/.*)?$/, 'fflate'] },
    sourcemap: true,
  },
})
