/** Demo app (`npm run demo`): Vite dev server with the packages from source. */

import { resolve } from 'node:path'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { sourceAliases } from '../aliases'

export default defineConfig({
  root: __dirname,
  plugins: [vue()],
  resolve: { alias: sourceAliases() },
  server: { port: 5199, fs: { allow: [resolve(__dirname, '../../..')] } },
  build: { outDir: resolve(__dirname, '../dist-demo'), emptyOutDir: true, chunkSizeWarningLimit: 2000 },
})
