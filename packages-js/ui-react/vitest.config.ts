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
      { find: /^@auditcore\/ui-core\/style\.css$/, replacement: fileURLToPath(new URL('../ui-core/styles/index.css', import.meta.url)) },
      { find: /^@auditcore\/ui-core$/, replacement: fileURLToPath(new URL('../ui-core/src/index.ts', import.meta.url)) },
      { find: /^@auditcore\/ui\/elements$/, replacement: ui('elements.ts') },
      { find: /^@auditcore\/ui$/, replacement: ui('index.ts') },
      { find: /^@auditcore\/kanban-core$/, replacement: fileURLToPath(new URL('../kanban-core/src/index.ts', import.meta.url)) },
      { find: /^@auditcore\/common\/browser$/, replacement: fileURLToPath(new URL('../common/src/browser.ts', import.meta.url)) },
      { find: /^@auditcore\/common$/, replacement: fileURLToPath(new URL('../common/src/index.ts', import.meta.url)) },
    ],
  },
  test: {
    environment: 'happy-dom',
    include: ['test/**/*.spec.ts', 'test/**/*.spec.tsx'],
    // Kein pauschal höheres Zeitlimit: Die Paritätsdateien setzen ihres gezielt in
    // test/parity/setup.ts; die Worker-Zahl in der CI passt scripts/js/vitest-workers.sh an.
  },
})
