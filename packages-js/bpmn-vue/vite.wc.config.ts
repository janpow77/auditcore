/**
 * Web component bundle: `dist-wc/flowaudit-bpmn-editor.js` – one ES module
 * with Vue, the core editor, the FlowAudit layer, bundled profiles and CSS.
 */

import { resolve } from 'node:path'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { sourceAliases } from './aliases.ts'
import { injectCss } from './cssInjection.ts'

export default defineConfig({
  plugins: [vue(), injectCss()],
  resolve: { alias: sourceAliases() },
  define: { 'process.env.NODE_ENV': JSON.stringify('production') },
  build: {
    outDir: 'dist-wc',
    emptyOutDir: true,
    cssCodeSplit: false,
    // App build (not library mode) so the self-contained bundle is fully minified.
    rolldownOptions: {
      input: resolve(import.meta.dirname, 'src/web-component/register.ts'),
      preserveEntrySignatures: 'strict',
      output: { format: 'es', entryFileNames: 'flowaudit-bpmn-editor.js', codeSplitting: false },
    },
    sourcemap: true,
    chunkSizeWarningLimit: 2000,
  },
})
