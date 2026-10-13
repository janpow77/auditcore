/**
 * Erzeugte Nachweise: `docs/abgleich.md` (Golden-Abgleich je Blatt) und die
 * Tabelle der begründeten Abweichungen in `docs/abweichungen.md`. Der Test
 * prüft, dass beide zum Code passen; `npm run docs:write` schreibt sie neu.
 * `SAMPLING_TEMPLATES_SKIP_DOCS=1` überspringt die Prüfung (paralleler Bau mehrerer Blätter).
 */
import { readFileSync, writeFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { describe, expect, it } from 'vitest'
import type { AvailableSheet } from '../src/model/sheet'
import { TEMPLATE_STRATA } from '../src/model/strata'
import { availableSheets } from '../src/sheets/registry'
import { TOLERANCE, compareCase, loadGolden, type CaseReport } from './golden'

const WRITE = process.env.SAMPLING_TEMPLATES_WRITE_DOCS === '1'
/** Während mehrere Blätter gleichzeitig entstehen, werden die Nachweise erst beim Zusammenführen erzeugt. */
const SKIP = process.env.SAMPLING_TEMPLATES_SKIP_DOCS === '1'
const path = (name: string): string => fileURLToPath(new URL(`../docs/${name}`, import.meta.url))
const START = '<!-- abweichungen:start – erzeugt mit `npm run docs:write`, nicht von Hand ändern -->'
const END = '<!-- abweichungen:end -->'

function reports(sheet: AvailableSheet): CaseReport[] {
  return loadGolden(sheet.id).map((golden) => compareCase(sheet, golden))
}

const total = (list: readonly CaseReport[], pick: (report: CaseReport) => number): number => list.reduce((sum, report) => sum + pick(report), 0)

function comparison(): string {
  const lines = [
    '# Abgleich der Rechenkerne mit der Vorlage',
    '',
    '<!-- Erzeugt mit `npm run docs:write -w @auditcore/sampling-templates-core`; nicht von Hand ändern. -->',
    '',
    'Je Fall werden die Eingaben in eine Kopie der Excel-Vorlage geschrieben, die Mappe wird mit LibreOffice',
    'neu berechnet (`scripts/golden_recalc.py`), und jede Formelzelle des Blatts wird mit dem Rechenkern verglichen:',
    `Zahlen mit relativer Toleranz ${TOLERANCE}, Texte wortgleich. „Begründet“ sind Zellen, an denen die Webfassung bei`,
    'leeren Eingaben „Angabe fehlt“ zeigt, während die Vorlage mit 0 weiterrechnet ([abweichungen.md](abweichungen.md)).',
    '',
    '| Blatt | Fälle | verglichene Zellen | übereinstimmend | begründete Abweichungen | unbegründete Abweichungen (Soll 0) |',
    '|---|---:|---:|---:|---:|---:|',
  ]
  const details: string[] = []
  for (const sheet of availableSheets()) {
    const list = reports(sheet)
    const compared = total(list, (report) => report.compared)
    const explained = total(list, (report) => report.explained.length)
    const unexplained = total(list, (report) => report.unexplained.length)
    lines.push(`| ${sheet.id} | ${list.length} | ${compared} | ${compared - explained - unexplained} | ${explained} | ${unexplained} |`)
    details.push('', `## ${sheet.id}`, '', '| Nr. | Fall | Zellen | begründet | unbegründet |', '|---:|---|---:|---:|---:|')
    list.forEach((report, index) => details.push(`| ${index + 1} | ${report.name} | ${report.compared} | ${report.explained.length} | ${report.unexplained.length} |`))
  }
  return `${[...lines, ...details].join('\n')}\n`
}

/** Zellen kompakt: vollständige Schichtzeilen der Vorlage als Bereich (`D35–J35`), sonst einzeln. */
function compact(cells: readonly string[]): string {
  const rest = new Set(cells)
  const ranges: string[] = []
  for (const cell of cells) {
    const row = cell.replace(/^[A-Z]+/, '')
    const strata = TEMPLATE_STRATA.map((column) => `${column}${row}`)
    if (cell !== strata[0] || !strata.every((entry) => rest.has(entry))) continue
    strata.forEach((entry) => rest.delete(entry))
    ranges.push(`${strata[0]}–${strata.at(-1)}`)
  }
  return [...cells.filter((cell) => rest.has(cell)), ...ranges].join(', ')
}

/** Abweichungen mit gleicher Ursache, Anzeige und Begründung stehen in einer Zeile. */
function deviationTable(): string {
  const lines: string[] = [START]
  for (const sheet of availableSheets()) {
    const groups = new Map<string, { cells: string[]; whenEmpty: readonly string[]; template: string; reason: string }>()
    for (const deviation of sheet.deviations) {
      const key = JSON.stringify([deviation.whenEmpty, deviation.template, deviation.reason])
      const group = groups.get(key) ?? { cells: [], whenEmpty: deviation.whenEmpty, template: deviation.template, reason: deviation.reason }
      group.cells.push(deviation.cell)
      groups.set(key, group)
    }
    lines.push('', `### ${sheet.id}`, '', '| Zellen | leer ist eine von | Vorlage zeigt | Webfassung zeigt | Begründung |', '|---|---|---|---|---|')
    for (const group of groups.values()) lines.push(`| ${compact(group.cells)} | ${compact(group.whenEmpty)} | ${group.template} | Angabe fehlt | ${group.reason} |`)
  }
  return [...lines, '', END].join('\n')
}

function withTable(document: string, table: string): string {
  const start = document.indexOf(START)
  const end = document.indexOf(END)
  if (start < 0 || end < 0) throw new Error('Markierungen für die Abweichungstabelle fehlen in docs/abweichungen.md')
  return document.slice(0, start) + table + document.slice(end + END.length)
}

describe.skipIf(SKIP)('Erzeugte Nachweise', () => {
  it('docs/abgleich.md entspricht dem Golden-Abgleich', () => {
    if (WRITE) writeFileSync(path('abgleich.md'), comparison())
    expect(readFileSync(path('abgleich.md'), 'utf8')).toBe(comparison())
  })

  it('die Abweichungstabelle in docs/abweichungen.md entspricht den Blattmodulen', () => {
    const current = readFileSync(path('abweichungen.md'), 'utf8')
    if (WRITE) writeFileSync(path('abweichungen.md'), withTable(current, deviationTable()))
    expect(readFileSync(path('abweichungen.md'), 'utf8')).toBe(withTable(current, deviationTable()))
  })
})
