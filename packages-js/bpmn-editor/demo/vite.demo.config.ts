import { defineConfig } from 'vite'

/** Demo-Bau für die Sichtprüfung im Browser. */
export default defineConfig({
  root: __dirname,
  base: './',
  build: { outDir: process.env.DEMO_OUT || 'dist-demo', emptyOutDir: true },
})
