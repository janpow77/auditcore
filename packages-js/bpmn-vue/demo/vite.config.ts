/** Demo app (`npm run demo`): Vite dev server with the packages from source. */

import { resolve } from 'node:path'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { sourceAliases } from '../aliases.ts'

export default defineConfig({
  root: import.meta.dirname,
  plugins: [vue()],
  resolve: { alias: sourceAliases() },
  server: { port: 5199, fs: { allow: [resolve(import.meta.dirname, '../../..')] } },
  build: { outDir: resolve(import.meta.dirname, '../dist-demo'), emptyOutDir: true, chunkSizeWarningLimit: 2000 },
})
