#!/usr/bin/env node
/**
 * Runs the tests of a React package against React 18.3: installs React 18
 * with Testing Library into a separate directory (outside the workspace, the
 * lockfile stays on React 19) and starts Vitest with `REACT_DIR`, which the
 * package's vitest.config.ts uses to resolve react, react-dom and
 * @testing-library/react. Usage (in the package directory):
 *   node ../../scripts/js/react18-test.mjs [vitest arguments]
 */
import { execFileSync } from 'node:child_process'
import { existsSync, mkdirSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'

const dir = process.env.REACT18_DIR ?? join(tmpdir(), 'auditcore-react18')
const PACKAGES = ['react@18.3.1', 'react-dom@18.3.1', '@testing-library/react@16.3.3', '@testing-library/dom@10.4.2']
const npm = process.platform === 'win32' ? 'npm.cmd' : 'npm'
const npx = process.platform === 'win32' ? 'npx.cmd' : 'npx'

if (!existsSync(join(dir, 'node_modules', 'react-dom', 'package.json'))) {
  mkdirSync(dir, { recursive: true })
  writeFileSync(join(dir, 'package.json'), JSON.stringify({ name: 'auditcore-react18', private: true }))
  execFileSync(npm, ['install', '--no-audit', '--no-fund', '--ignore-scripts', ...PACKAGES], { cwd: dir, stdio: 'inherit' })
}

execFileSync(npx, ['vitest', 'run', ...process.argv.slice(2)], { stdio: 'inherit', env: { ...process.env, REACT_DIR: dir } })
