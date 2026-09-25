/**
 * Standalone app: static files in `dist-standalone/` (relative paths, no
 * CDN) to be served by any web server or embedded in the Python package.
 */

import { resolve } from 'node:path'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { sourceAliases } from './aliases'

export default defineConfig({
  root: resolve(__dirname, 'standalone'),
  base: './',
  plugins: [vue()],
  resolve: { alias: sourceAliases() },
  build: {
    outDir: resolve(__dirname, 'dist-standalone'),
    emptyOutDir: true,
    sourcemap: false,
    chunkSizeWarningLimit: 2000,
  },
})
