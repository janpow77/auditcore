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
import { STRATA_COLUMNS, TEMPLATE_STRATA } from '../src/model/strata'
import { availableSheets } from '../src/sheets/registry'
import { LEGACY_STRATA } from '../src/sheets/shared/legacy'
import { AMOUNT_TOLERANCE, TOLERANCE, compareCase, goldenFiles, templateMismatches, type CaseReport, type GoldenCase } from './golden'

const WRITE = process.env.SAMPLING_TEMPLATES_WRITE_DOCS === '1'
/** Während mehrere Blätter gleichzeitig entstehen, werden die Nachweise erst beim Zusammenführen erzeugt. */
const SKIP = process.env.SAMPLING_TEMPLATES_SKIP_DOCS === '1'
const path = (name: string): string => fileURLToPath(new URL(`../docs/${name}`, import.meta.url))
const START = '<!-- abweichungen:start – erzeugt mit `npm run docs:write`, nicht von Hand ändern -->'
const END = '<!-- abweichungen:end -->'

/** Fälle eines Blatts je Golden-Datei: der Hauptsatz `<Blatt>.golden.json` und weitere Sätze (`.zufall`, `.pruefer`). */
function caseSets(sheet: AvailableSheet): { name: string; cases: GoldenCase[] }[] {
  return goldenFiles(sheet.id).map((file) => ({
    name: file.replace(`${sheet.id}.`, '').replace(/\.?golden\.json$/, '') || 'Hauptsatz',
    cases: JSON.parse(readFileSync(fileURLToPath(new URL(`./golden/${file}`, import.meta.url)), 'utf8')) as GoldenCase[],
  }))
}

const total = (list: readonly CaseReport[], pick: (report: CaseReport) => number): number => list.reduce((sum, report) => sum + pick(report), 0)

interface Counts {
  cases: number
  compared: number
  explained: number
  /** Würdigungen an der Toleranzkante bei 17-stelliger Eingabe. */
  edge: number
  unexplained: number
  /** Abweichungen unter der Richtlinie „wie die Vorlage“. */
  template: number
}

function countsOf(sheet: AvailableSheet, cases: readonly GoldenCase[]): Counts & { reports: CaseReport[] } {
  const list = cases.map((golden) => compareCase(sheet, golden))
  return {
    cases: list.length,
    compared: total(list, (report) => report.compared),
    explained: total(list, (report) => report.explained.length),
    edge: total(list, (report) => report.edge.length),
    unexplained: total(list, (report) => report.unexplained.length),
    template: cases.reduce((sum, golden) => sum + templateMismatches(sheet, golden).length, 0),
    reports: list,
  }
}

const add = (left: Counts, right: Counts): Counts => ({
  cases: left.cases + right.cases,
  compared: left.compared + right.compared,
  explained: left.explained + right.explained,
  edge: left.edge + right.edge,
  unexplained: left.unexplained + right.unexplained,
  template: left.template + right.template,
})

const row = (name: string, counts: Counts): string =>
  `| ${name} | ${counts.cases} | ${counts.compared} | ${counts.compared - counts.explained - counts.edge - counts.unexplained} | ${counts.explained} | ${counts.edge} | ${counts.unexplained} | ${counts.template} |`

const EMPTY: Counts = { cases: 0, compared: 0, explained: 0, edge: 0, unexplained: 0, template: 0 }
const HEAD = ['| Fälle | verglichene Zellen | übereinstimmend | begründete Abweichungen | Toleranzkante | unbegründete Abweichungen (Soll 0) | Abweichungen „wie die Vorlage“ (Soll 0) |', '|---:|---:|---:|---:|---:|---:|---:|']

function comparison(): string {
  const lines = [
    '# Abgleich der Rechenkerne mit der Vorlage',
    '',
    '<!-- Erzeugt mit `npm run docs:write -w @auditcore/sampling-templates-core`; nicht von Hand ändern. -->',
    '',
    'Je Fall werden die Eingaben in eine Kopie der Excel-Vorlage geschrieben, die Mappe wird mit LibreOffice',
    'neu berechnet (`scripts/golden_recalc.py`), und jede Formelzelle des Blatts wird mit dem Rechenkern verglichen:',
    `Zellen mit Ganzzahlformat genau, übrige Zahlen mit relativer Toleranz ${TOLERANCE}, Texte wortgleich.`,
    `Bei Eurobeträgen gilt zusätzlich ein absoluter Unterschied bis ${AMOUNT_TOLERANCE} € als gleich (Rauschen aus einer`,
    'Auslöschung, Blatt 20 G43). Werte ab 10¹⁵ liegen außerhalb des geprüften Zahlenbereichs: Dort wird nur die',
    'Größenordnung verglichen (relativ 0,001), und die Webfassung weist das Ergebnis als nicht belastbar aus.',
    '',
    '**Grenze dieses Nachweises:** Alle Sollwerte stammen aus der Neuberechnung der Vorlage mit LibreOffice 24.2.',
    'Eine Gegenprobe mit Microsoft Excel steht aus. Vergleichstoleranz (2⁻⁴⁸), `AUFRUNDEN` (Kürzung auf zwölf geltende',
    'Stellen) und die Summation mit Fehlerausgleich sind an LibreOffice gemessen; ob Excel an Schwellen und beim',
    'Aufrunden in jedem Fall gleich entscheidet, ist nicht geprüft.',
    '',
    '- **Begründet** sind Zellen, an denen die Webfassung nach der geltenden Richtlinie für fehlende Angaben keinen Wert',
    '  zeigt, während die Vorlage einen zeigt ([abweichungen.md](abweichungen.md)); die Gegenprobe ist bestanden. Seit der',
    '  Regel „bei vollständigen Pflichteingaben immer wie die Vorlage“ entstehen sie nur noch, wo eine Eingabe fehlt.',
    '- **Toleranzkante** sind Würdigungen, bei denen die Quote genau auf der Vergleichstoleranz liegt und der Fall eine',
    '  Eingabe mit 16 oder 17 geltenden Stellen trägt (Prüfsonde der Abnahme). Geprüft ist je Zelle: Mit der um höchstens',
    '  zwei letzte Stellen verschobenen Eingabe zeigt die Webfassung genau den Text der Vorlage. Über die Oberfläche lässt',
    '  sich eine solche Zahl nicht eingeben.',
    '- **„Wie die Vorlage“** ist dieselbe Rechnung unter der Richtlinie `TEMPLATE_POLICY` (jede fehlende Angabe mit 0',
    '  gerechnet): Dann muss jede Zelle den Wert der Vorlage zeigen.',
    '- Die Fallsätze `abnahme-grund`, `abnahme-luecken` und `abnahme-schwelle` sind die 6.805 Fälle der unabhängigen',
    '  Gesamtabnahme (eigener Generator, Einzellücken-Matrix, Schwellen- und Ganzzahlsonden).',
    '',
    `| Blatt ${HEAD[0]}`,
    `|---${HEAD[1]}`,
  ]
  const details: string[] = []
  let sum = EMPTY
  for (const sheet of availableSheets()) {
    const sets = caseSets(sheet).map((set) => ({ name: set.name, ...countsOf(sheet, set.cases) }))
    const counts = sets.reduce<Counts>(add, EMPTY)
    sum = add(sum, counts)
    lines.push(row(sheet.id, counts))
    details.push('', `## ${sheet.id}`, '', `| Fallsatz ${HEAD[0]}`, `|---${HEAD[1]}`, ...sets.map((set) => row(set.name, set)))
    const main = sets.find((set) => set.name === 'Hauptsatz')
    if (!main) continue
    details.push('', '| Nr. | Fall (Hauptsatz) | Zellen | begründet | unbegründet |', '|---:|---|---:|---:|---:|')
    main.reports.forEach((report, index) => details.push(`| ${index + 1} | ${report.name} | ${report.compared} | ${report.explained.length} | ${report.unexplained.length} |`))
  }
  lines.push(row('**Summe**', sum))
  return `${[...lines, ...details].join('\n')}\n`
}

/** Spaltensätze, die als Bereich zusammengefasst werden: alle Schichten der Webfassung, sonst die sieben der Vorlage. */
const COLUMN_SETS: readonly (readonly string[])[] = [STRATA_COLUMNS, LEGACY_STRATA, TEMPLATE_STRATA, LEGACY_STRATA.slice(0, TEMPLATE_STRATA.length)]

/** Bereich einer Schichtzeile: `D35–J35`, mit den Spalten der Webfassung `D35–J35, AA35–AM35`. */
function rangeOf(columns: readonly string[], row: string): string {
  const template = columns.slice(0, TEMPLATE_STRATA.length)
  const extra = columns.slice(TEMPLATE_STRATA.length)
  const span = (part: readonly string[]): string => `${part[0]}${row}–${part.at(-1)}${row}`
  return extra.length ? `${span(template)}, ${span(extra)}` : span(template)
}

/** Zellen kompakt: vollständige Schichtzeilen als Bereich, sonst einzeln. */
function compact(cells: readonly string[]): string {
  const rest = new Set(cells)
  const ranges: string[] = []
  for (const cell of cells) {
    const row = cell.replace(/^[A-Z]+/, '')
    const columns = COLUMN_SETS.find((set) => cell === `${set[0]}${row}` && set.every((column) => rest.has(`${column}${row}`)))
    if (!columns) continue
    columns.forEach((column) => rest.delete(`${column}${row}`))
    ranges.push(rangeOf(columns, row))
  }
  return [...cells.filter((cell) => rest.has(cell)), ...ranges].join(', ')
}

const STRATUM_COLUMNS: ReadonlySet<string> = new Set([...STRATA_COLUMNS, ...LEGACY_STRATA])

/** Was die Webfassung nach der geltenden Richtlinie zeigt. */
const SHOWN = { requiredInput: 'Angabe fehlt', withoutBasis: 'kein Wert' } as const

/** Abweichungen mit gleicher Ursache, Anzeige und Begründung stehen in einer Zeile. */
function deviationTable(): string {
  const lines: string[] = [START]
  for (const sheet of availableSheets()) {
    const groups = new Map<string, { cells: string[]; whenEmpty: readonly string[]; template: string; reason: string; kind: keyof typeof SHOWN }>()
    for (const deviation of sheet.deviations) {
      const kind = deviation.kind ?? 'requiredInput'
      // Schichtzeilen: Einträge, die sich nur in der Schichtspalte unterscheiden, stehen in einer Zeile.
      const inStratum = STRATUM_COLUMNS.has(deviation.cell.replace(/\d+$/, ''))
      const causes = inStratum ? deviation.whenEmpty.map((reference) => (reference.includes('!') ? reference : reference.replace(/^[A-Z]+/, ''))) : deviation.whenEmpty
      const key = JSON.stringify([causes, deviation.template, deviation.reason, kind])
      const group = groups.get(key) ?? { cells: [], whenEmpty: [], template: deviation.template, reason: deviation.reason, kind }
      group.cells.push(deviation.cell)
      group.whenEmpty = [...new Set([...group.whenEmpty, ...deviation.whenEmpty])]
      groups.set(key, group)
    }
    lines.push('', `### ${sheet.id}`, '', '| Zellen | leer ist eine von | Vorlage zeigt | Webfassung zeigt | Begründung |', '|---|---|---|---|---|')
    for (const group of groups.values()) lines.push(`| ${compact(group.cells)} | ${compact(group.whenEmpty)} | ${group.template} | ${SHOWN[group.kind]} | ${group.reason} |`)
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
    const expected = comparison()
    if (WRITE) writeFileSync(path('abgleich.md'), expected)
    expect(readFileSync(path('abgleich.md'), 'utf8')).toBe(expected)
  }, 180_000)

  it('die Abweichungstabelle in docs/abweichungen.md entspricht den Blattmodulen', () => {
    const current = readFileSync(path('abweichungen.md'), 'utf8')
    if (WRITE) writeFileSync(path('abweichungen.md'), withTable(current, deviationTable()))
    expect(readFileSync(path('abweichungen.md'), 'utf8')).toBe(withTable(current, deviationTable()))
  })
})
