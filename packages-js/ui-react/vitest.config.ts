import { fileURLToPath } from 'node:url'
import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vitest/config'

const ui = (path: string): string => fileURLToPath(new URL(`../ui/src/${path}`, import.meta.url))

// Andere React-Version (scripts/js/react19-test.mjs bzw. react18-test.mjs): react, react-dom und
// Testing Library aus `REACT_DIR` statt aus dem Workspace.
const reactDir = process.env.REACT_DIR
const reactAliases = reactDir
  ? [
      { find: /^react-dom(\/.*)?$/, replacement: `${reactDir}/node_modules/react-dom$1` },
      { find: /^react(\/.*)?$/, replacement: `${reactDir}/node_modules/react$1` },
      { find: /^@testing-library\/react$/, replacement: `${reactDir}/node_modules/@testing-library/react` },
    ]
  : []

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: [
      ...reactAliases,
      { find: /^@flowaudit\/ui-core\/style\.css$/, replacement: fileURLToPath(new URL('../ui-core/styles/index.css', import.meta.url)) },
      { find: /^@flowaudit\/ui-core$/, replacement: fileURLToPath(new URL('../ui-core/src/index.ts', import.meta.url)) },
      { find: /^@flowaudit\/ui\/elements$/, replacement: ui('elements.ts') },
      { find: /^@flowaudit\/ui$/, replacement: ui('index.ts') },
      { find: /^@flowaudit\/kanban-core$/, replacement: fileURLToPath(new URL('../kanban-core/src/index.ts', import.meta.url)) },
      { find: /^@flowaudit\/common\/browser$/, replacement: fileURLToPath(new URL('../common/src/browser.ts', import.meta.url)) },
      { find: /^@flowaudit\/common$/, replacement: fileURLToPath(new URL('../common/src/index.ts', import.meta.url)) },
    ],
  },
  test: {
    environment: 'happy-dom',
    include: ['test/**/*.spec.ts', 'test/**/*.spec.tsx'],
    // Paritätsabläufe rendern Vue und React nacheinander; auf ausgelasteten
    // CI-Runnern (Node 20) dauerten einzelne länger als die Vorgabe von 5 s.
    testTimeout: 20_000,
  },
})
