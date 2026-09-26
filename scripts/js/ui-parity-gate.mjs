#!/usr/bin/env node
/**
 * Vollständigkeits-Gate Vue ↔ React (fail closed).
 *
 * Leitet aus den Quellen ab, welche öffentlichen Oberflächenkomponenten es in
 * den Vue-Paketen gibt (packages-js/ui: Exporte und `ELEMENTS`;
 * packages-js/bpmn-vue: Exporte und Web Component), und prüft je Komponente
 * bzw. Gruppe:
 *
 *   react-missing    native React-Fassung in packages-js/ui-react bzw. packages-js/bpmn-react
 *   vue-missing      umgekehrt: keine React-Komponente ohne Vue-Gegenstück
 *   core-*           Kernmodul ui-core/src/<gruppe>/ (exportiert, mit Controller, Stil)
 *                    bzw. Controller in bpmn-flowaudit/src/ui
 *   parity-cases     cases-<gruppe>.ts, importiert von einem Vue- und einem React-Paritätstest
 *   vue-import       keine Vue-Imports/-Abhängigkeiten im React-Paket
 *
 * Ausnahmen nur über quality/ui-parity-exceptions.json (Begründung, Ablaufdatum,
 * mit --compare-ref nur Abbau). Siehe docs/ui/beitragen.md.
 *
 * Aufruf: node scripts/js/ui-parity-gate.mjs [--root <dir>] [--compare-ref <git-ref>] [--json <datei>]
 */
import { writeFileSync } from 'node:fs'
import { dirname, join, resolve } from 'node:path'
import process from 'node:process'
import { fileURLToPath } from 'node:url'
import { checkFamily, testImports } from './ui-parity/checks.mjs'
import { applyExceptions, EXCEPTIONS_FILE, exceptionsAt, loadExceptions, ratchetProblems } from './ui-parity/exceptions.mjs'
import { FAMILIES } from './ui-parity/families.mjs'

const DEFAULT_ROOT = join(dirname(fileURLToPath(import.meta.url)), '..', '..')

function parseArgs(argv) {
  const options = { root: DEFAULT_ROOT, compareRef: null, json: null, today: null }
  for (let index = 0; index < argv.length; index += 1) {
    const flag = argv[index]
    const value = argv[index + 1]
    if (flag === '--root') options.root = resolve(value)
    else if (flag === '--compare-ref') options.compareRef = value
    else if (flag === '--json') options.json = value
    else if (flag === '--today') options.today = value
    else throw new Error(`Unbekannte Option: ${flag}`)
    index += 1
  }
  return options
}

/**
 * Gate ausführen und Bericht liefern (ohne Ausgabe; für Tests und CLI).
 * @param {{ root: string, compareRef?: string | null, today?: string | null, families?: typeof FAMILIES }} options
 */
export function runGate(options) {
  const root = resolve(options.root)
  const today = new Date(`${options.today ?? new Date().toISOString().slice(0, 10)}T00:00:00Z`)
  const tests = testImports(root)
  const results = (options.families ?? FAMILIES).map((family) => checkFamily(root, family, tests))
  const violations = results.flatMap((result) => result.violations).sort((a, b) => (a.id < b.id ? -1 : 1))
  const exceptions = loadExceptions(join(root, EXCEPTIONS_FILE))
  const { open, excepted, problems } = applyExceptions(violations, exceptions, today)
  const base = options.compareRef ? exceptionsAt(root, options.compareRef) : null
  problems.push(...ratchetProblems(exceptions, base))
  return {
    scope: 'AUDITCORE_UI_PARITY_GATE',
    status: open.length === 0 && problems.length === 0 ? 'PASS' : 'FAIL',
    families: results.map((result) => result.summary),
    open,
    excepted,
    problems,
    ratchet: options.compareRef ? (base === null ? 'Vergleichsstand ohne Ausnahmedatei (Erstanlage)' : `gegen ${options.compareRef}`) : 'ohne Vergleichsstand',
  }
}

function print(report) {
  for (const family of report.families) {
    console.log(`${family.family}: ${family.vueComponents} Vue-Komponenten, ${family.reactComponents} React-Komponenten, Gruppen: ${family.groups.join(', ')}`)
  }
  for (const item of report.excepted) console.log(`  Ausnahme  ${item.id}`)
  for (const item of report.open) console.log(`::error::${item.id} – ${item.message}`)
  for (const problem of report.problems) console.log(`::error::${EXCEPTIONS_FILE}: ${problem}`)
  console.log(`Ratchet: ${report.ratchet}`)
  console.log(`UI-Paritäts-Gate: ${report.status} (${report.open.length} offene Lücken, ${report.excepted.length} befristete Ausnahmen, ${report.problems.length} Ausnahmefehler)`)
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  try {
    const options = parseArgs(process.argv.slice(2))
    const report = runGate(options)
    print(report)
    if (options.json) writeFileSync(options.json, `${JSON.stringify(report, null, 2)}\n`)
    process.exit(report.status === 'PASS' ? 0 : 1)
  } catch (error) {
    console.log(`::error::UI-Paritäts-Gate: ${error instanceof Error ? error.message : String(error)}`)
    process.exit(1)
  }
}
