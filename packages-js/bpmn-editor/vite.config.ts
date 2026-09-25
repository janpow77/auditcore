import { defineConfig } from 'vite'
import dts from 'vite-plugin-dts'

/** Bibliotheksbau: ESM und Typdeklarationen; Abhängigkeiten bleiben extern. */
export default defineConfig({
  build: {
    target: 'es2022',
    sourcemap: true,
    emptyOutDir: true,
    lib: {
      entry: 'src/index.ts',
      formats: ['es'],
      fileName: 'index',
      cssFileName: 'bpmn-editor',
    },
    rollupOptions: {
      external: [/^diagram-js(\/.*)?$/, /^bpmn-moddle(\/.*)?$/, 'didi', 'min-dash', 'min-dom', 'tiny-svg'],
    },
  },
  plugins: [dts({ tsconfigPath: './tsconfig.build.json', entryRoot: 'src' })],
})
