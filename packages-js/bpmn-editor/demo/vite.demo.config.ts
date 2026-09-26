import { defineConfig } from 'vite'

/** Demo-Bau für die Sichtprüfung im Browser. */
export default defineConfig({
  root: import.meta.dirname,
  base: './',
  build: { outDir: process.env.DEMO_OUT || 'dist-demo', emptyOutDir: true },
})
