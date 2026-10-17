/** Demo (`npm run demo`): Vite mit den Paketen aus dem Quelltext; der Bau trägt eine strenge Content-Security-Policy. */
import { resolve } from 'node:path'
import vue from '@vitejs/plugin-vue'
import { defineConfig, type Plugin } from 'vite'
import { sourceAliases } from '../aliases.ts'

const CSP = "default-src 'self'; img-src 'self' data: blob:; object-src 'none'; base-uri 'self'; form-action 'none'"

/** Nur im Bau: Der Entwicklungsserver braucht Inline-Skripte und WebSockets. */
function contentSecurityPolicy(): Plugin {
  return {
    name: 'sampling-templates-demo-csp',
    apply: 'build',
    transformIndexHtml: (html) => html.replace('<meta charset="utf-8" />', `<meta charset="utf-8" />\n    <meta http-equiv="Content-Security-Policy" content="${CSP}" />`),
  }
}

export default defineConfig({
  root: import.meta.dirname,
  base: './',
  plugins: [vue(), contentSecurityPolicy()],
  resolve: { alias: sourceAliases },
  server: { port: 5196, fs: { allow: [resolve(import.meta.dirname, '../../..')] } },
  preview: { port: 5196 },
  build: { outDir: resolve(import.meta.dirname, '../dist-demo'), emptyOutDir: true },
})
