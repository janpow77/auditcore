#!/usr/bin/env node
/**
 * Führt die Tests eines React-Pakets gegen React 19 aus: installiert React 19
 * mit Testing Library in ein eigenes Verzeichnis (außerhalb des Workspaces,
 * das Lockfile bleibt unverändert) und startet Vitest mit `REACT_DIR`, über
 * das die vitest.config.ts des Pakets react, react-dom und
 * @testing-library/react auflöst. Gegenstück zu `react18-test.mjs`.
 * Aufruf (im Paketverzeichnis): node ../../scripts/js/react19-test.mjs [Vitest-Argumente]
 */
import { execFileSync } from 'node:child_process'
import { existsSync, mkdirSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'

const dir = process.env.REACT19_DIR ?? join(tmpdir(), 'auditcore-react19')
const PACKAGES = ['react@19.3.0', 'react-dom@19.3.0', '@testing-library/react@16.3.3', '@testing-library/dom@10.4.2']
const npm = process.platform === 'win32' ? 'npm.cmd' : 'npm'
const npx = process.platform === 'win32' ? 'npx.cmd' : 'npx'

if (!existsSync(join(dir, 'node_modules', 'react-dom', 'package.json'))) {
  mkdirSync(dir, { recursive: true })
  writeFileSync(join(dir, 'package.json'), JSON.stringify({ name: 'auditcore-react19', private: true }))
  execFileSync(npm, ['install', '--no-audit', '--no-fund', '--ignore-scripts', ...PACKAGES], { cwd: dir, stdio: 'inherit' })
}

execFileSync(npx, ['vitest', 'run', ...process.argv.slice(2)], { stdio: 'inherit', env: { ...process.env, REACT_DIR: dir } })
