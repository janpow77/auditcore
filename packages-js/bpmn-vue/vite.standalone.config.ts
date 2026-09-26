/**
 * Standalone app: static files in `dist-standalone/` (relative paths, no
 * CDN) to be served by any web server or embedded in the Python package.
 */

import { resolve } from 'node:path'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { sourceAliases } from './aliases.ts'

export default defineConfig({
  root: resolve(import.meta.dirname, 'standalone'),
  base: './',
  plugins: [vue()],
  resolve: { alias: sourceAliases() },
  build: {
    outDir: resolve(import.meta.dirname, 'dist-standalone'),
    emptyOutDir: true,
    sourcemap: false,
    chunkSizeWarningLimit: 2000,
  },
})
