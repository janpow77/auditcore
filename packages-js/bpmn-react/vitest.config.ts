import { createRequire } from 'node:module'
import { dirname } from 'node:path'
import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vitest/config'
import { sourceAliases } from './aliases'

// One React for the components and @testing-library/react: the version this
// package resolves (devDependency 19). `REACT_DIR` points to another
// installation for the run against React 18 (`npm run test:react18`).
const require = createRequire(import.meta.url)
const packageDir = (name: string) => dirname(require.resolve(`${name}/package.json`, { paths: [process.env.REACT_DIR ?? __dirname] }))
const sources = Object.entries(sourceAliases()).map(([find, replacement]) => ({ find: new RegExp(`^${find.replace(/[/.]/g, '\\$&')}$`), replacement }))

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: [
      ...sources,
      // ESM build, so the React aliases below also apply inside the library.
      { find: /^@testing-library\/react$/, replacement: `${packageDir('@testing-library/react')}/dist/@testing-library/react.esm.js` },
      { find: /^react-dom(\/.*)?$/, replacement: `${packageDir('react-dom')}$1` },
      { find: /^react(\/.*)?$/, replacement: `${packageDir('react')}$1` },
    ],
  },
  esbuild: { jsx: 'automatic' },
  test: {
    environment: 'happy-dom',
    include: ['test/**/*.spec.tsx', 'test/**/*.spec.ts'],
    setupFiles: ['../bpmn-flowaudit/test/setup/svgTransforms.ts'],
    server: { deps: { inline: ['@testing-library/react'] } },
  },
})
