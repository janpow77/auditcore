#!/usr/bin/env node
/**
 * Lizenzprüfung der JavaScript-Pakete (packages-js) anhand der package-lock.json.
 *
 * - Verboten sind bpmn-js* , bpmn-font und @bpmn-io/properties-panel (andere
 *   Lizenz mit Wasserzeichenpflicht; Clean-Room-Regel des Editors).
 * - Laufzeitabhängigkeiten: nur MIT, ISC, BSD-2-Clause, BSD-3-Clause, Apache-2.0.
 * - Entwicklungswerkzeuge: zusätzlich ausdrücklich gelistete freizügige Lizenzen
 *   sowie Einzelfreigaben je Paket (DEV_EXCEPTIONS, z. B. lightningcss unter MPL-2.0).
 * - Eigene Workspace-Pakete müssen MIT sein.
 *
 * Aufruf: `npm run license-check` (Rückgabewert ≠ 0 bei Verstoß).
 */

import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, join } from 'node:path'

const root = join(dirname(fileURLToPath(import.meta.url)), '..', '..')
const lock = JSON.parse(readFileSync(join(root, 'package-lock.json'), 'utf8'))

const FORBIDDEN = [/^bpmn-js(-|$)/, /^bpmn-font$/, /^@bpmn-io\/properties-panel$/]
const RUNTIME_ALLOWED = new Set(['MIT', 'ISC', 'BSD-2-Clause', 'BSD-3-Clause', 'Apache-2.0'])
// Nur für Entwicklungswerkzeuge (Linter, Testumgebung, Bau); gelangen nicht ins Paket.
const DEV_ALLOWED = new Set([...RUNTIME_ALLOWED, 'MIT-0', '0BSD', 'BlueOak-1.0.0', 'Python-2.0', 'CC0-1.0'])
// Einzelfreigaben für Entwicklungswerkzeuge mit schwachem Copyleft: nur das genannte Paket,
// nur als Entwicklungsabhängigkeit. lightningcss (MPL-2.0) ist feste Abhängigkeit von Vite 8
// (CSS-Verarbeitung beim Bau); ausgeliefert wird nur das erzeugte CSS, kein lightningcss-Code.
const DEV_EXCEPTIONS = [{ name: /^lightningcss(-[a-z0-9-]+)?$/, license: 'MPL-2.0' }]

const problems = []
const runtime = new Map()

for (const [path, entry] of Object.entries(lock.packages || {})) {
  if (!path || entry.link) continue
  const name = entry.name || path.replace(/^.*node_modules\//, '')
  if (FORBIDDEN.some((pattern) => pattern.test(name))) problems.push(`verboten: ${name} (${path})`)
  if (!path.includes('node_modules/')) {
    if (entry.license !== 'MIT') problems.push(`Workspace-Paket ohne MIT-Lizenz: ${path} (${entry.license || 'keine'})`)
    continue
  }
  const license = entry.license || 'UNBEKANNT'
  const allowed = entry.dev ? DEV_ALLOWED : RUNTIME_ALLOWED
  const excepted = entry.dev && DEV_EXCEPTIONS.some((rule) => rule.name.test(name) && rule.license === license)
  if (!allowed.has(license) && !excepted) problems.push(`${entry.dev ? 'Entwicklung' : 'Laufzeit'}: ${name} → ${license}`)
  if (!entry.dev) runtime.set(name, `${entry.version} (${license})`)
}

if (process.argv.includes('--list')) {
  for (const [name, info] of [...runtime].sort()) console.log(`${name} ${info}`)
}

if (problems.length) {
  console.error('Lizenzprüfung fehlgeschlagen:')
  for (const problem of problems) console.error(`  - ${problem}`)
  process.exit(1)
}
console.log(`Lizenzprüfung bestanden: ${runtime.size} Laufzeitabhängigkeiten, keine verbotenen Pakete.`)
