/**
 * Temporäre Kopie des JS-Workspaces für Generator- und Gate-Tests: Quellen,
 * Tests, Doku und Konfiguration werden kopiert, `node_modules` verlinkt
 * (die tsconfig-Pfade und Vitest-Aliasse zeigen relativ auf die Kopie).
 */
import { cpSync, existsSync, mkdtempSync, readdirSync, symlinkSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { basename, join } from 'node:path'

const SKIPPED = new Set(['node_modules', 'dist', 'coverage', 'e2e-results', 'test-results', 'playwright-report'])
const COPIED = ['packages-js', 'scripts/js', 'scripts/docs', 'docs/ui', 'docs/bibliotheken', 'quality', 'package.json', 'tsconfig.base.json', 'eslint.config.mjs']

export function copyWorkspace(root, prefix = 'ui-parity-') {
  const target = mkdtempSync(join(process.env.UI_PARITY_TMP ?? tmpdir(), prefix))
  for (const path of COPIED) {
    if (!existsSync(join(root, path))) continue
    cpSync(join(root, path), join(target, path), {
      recursive: true,
      filter: (source) => !SKIPPED.has(basename(source)) && !basename(source).startsWith('dist-'),
    })
  }
  if (existsSync(join(root, 'node_modules'))) symlinkSync(join(root, 'node_modules'), join(target, 'node_modules'), 'dir')
  for (const name of readdirSync(join(root, 'packages-js'))) {
    const modules = join(root, 'packages-js', name, 'node_modules')
    if (existsSync(modules)) symlinkSync(modules, join(target, 'packages-js', name, 'node_modules'), 'dir')
  }
  return target
}
