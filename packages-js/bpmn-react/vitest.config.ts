import { createRequire } from 'node:module'
import { dirname, resolve } from 'node:path'
import { defineConfig } from 'vitest/config'

// One React for the wrapper and @testing-library/react: the version this
// package resolves (devDependency 18.3; REACT_DIR allows a run against 19).
const require = createRequire(import.meta.url)
const packageDir = (name: string) => dirname(require.resolve(`${name}/package.json`, { paths: [process.env.REACT_DIR ?? __dirname] }))

export default defineConfig({
  resolve: {
    alias: [
      { find: '@flowaudit/bpmn-flowaudit', replacement: resolve(__dirname, '../bpmn-flowaudit/src/index.ts') },
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
    server: { deps: { inline: ['@testing-library/react'] } },
  },
})
