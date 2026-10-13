/**
 * Abgleich eines Rechenkerns mit den Golden-Dateien: jede Formelzelle des
 * Blatts mit relativer Toleranz 1e-9, Texte wortgleich. Eine Abweichung ist nur
 * zulässig, wenn das Blatt sie als begründete Abweichung führt (`deviations`).
 */
import { readFileSync, readdirSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { isNumber } from '../src/excel/index'
import { defaultInputs, findField } from '../src/model/definition'
import { SUMMARY_CELLS, createContext, isEmptyReference, type AvailableSheet, type SheetModule } from '../src/model/sheet'
import type { CellMap, CellValue, Deviation } from '../src/model/types'
import { SHEETS, availableSheets } from '../src/sheets/registry'
import { computeWorkspace } from '../src/workspace/compute'
import { emptyWorkspace, type WorkspaceState } from '../src/workspace/types'

export const TOLERANCE = 1e-9

export interface GoldenCase {
  name: string
  blatt: string
  eingaben: Record<string, CellValue>
  erwartet: Record<string, CellValue>
}

export interface Mismatch {
  cell: string
  expected: CellValue
  actual: CellValue
}

export interface CaseReport {
  name: string
  compared: number
  /** Zellen, die als begründete Abweichung geführt sind. */
  explained: (Mismatch & { deviation: Deviation })[]
  /** Abweichungen ohne Begründung – Soll: keine. */
  unexplained: Mismatch[]
}

const GOLDEN_DIRECTORY = fileURLToPath(new URL('./golden/', import.meta.url))

/** Golden-Dateien eines Blatts: `<Blatt>.golden.json` und weitere Sätze `<Blatt>.<name>.golden.json`. */
export function goldenFiles(sheet: string): string[] {
  return readdirSync(GOLDEN_DIRECTORY)
    .filter((name) => name === `${sheet}.golden.json` || (name.startsWith(`${sheet}.`) && name.endsWith('.golden.json')))
    .sort()
}

export function loadGolden(sheet: string): GoldenCase[] {
  return goldenFiles(sheet).flatMap((name) => JSON.parse(readFileSync(`${GOLDEN_DIRECTORY}${name}`, 'utf8')) as GoldenCase[])
}

/** Zahlen mit relativer Toleranz, Texte wortgleich. `exact`: Ganzzahlzellen (Stichprobenumfänge) müssen genau stimmen. */
export function sameValue(expected: CellValue, actual: CellValue, exact = false): boolean {
  // Jenseits von 15 Stellen speichert die neu berechnete Mappe den Wert nicht mehr genau.
  if (isNumber(expected) && isNumber(actual)) return exact && Math.abs(expected) < 1e15 ? expected === actual : Math.abs(expected - actual) <= TOLERANCE * Math.max(1, Math.abs(expected))
  return (expected ?? null) === (actual ?? null)
}

/** Zelle mit ganzzahligem Format (`#,##0`): Der Abgleich verlangt den genauen Wert. */
export function isIntegerCell(sheet: AvailableSheet, cell: string): boolean {
  return findField(sheet.definition, cell)?.type === 'integer' || cell === SUMMARY_CELLS.sampleSize
}

/**
 * Arbeitsstand eines Falls: Jedes Blatt mit Rechenkern trägt die Vorgaben der
 * Vorlage, darüber die Werte des Falls (`null` leert eine Vorgabe). Zellen ohne
 * Blattangabe gehören zum Blatt des Falls, `Blatt!Zelle` schreibt in ein anderes.
 */
export function caseState(sheet: AvailableSheet, golden: GoldenCase, sheets: readonly SheetModule[] = SHEETS): WorkspaceState {
  const inputs: Record<string, Record<string, CellValue>> = {}
  for (const other of availableSheets(sheets)) {
    if (other.definition.layout !== 'list') inputs[other.id] = { ...defaultInputs(other.definition) }
  }
  for (const [reference, value] of Object.entries(golden.eingaben)) {
    const [name, cell] = reference.includes('!') ? (reference.split('!') as [string, string]) : [sheet.id, reference]
    const target = inputs[name]
    if (target) target[cell] = value
  }
  return { ...emptyWorkspace(), activeMethod: sheet.id, sheets: inputs }
}

/** Eingaben des Blatts selbst (für Tests, die nur ein Blatt rechnen). */
export function caseInputs(sheet: AvailableSheet, golden: GoldenCase): CellMap {
  return caseState(sheet, golden).sheets[sheet.id] as CellMap
}

/** Rechnet das Blatt noch einmal, wobei die genannten leeren Eingaben wie in der Vorlage als 0 zählen. */
function withZeros(sheet: AvailableSheet, golden: GoldenCase, references: readonly string[], all: Record<string, CellMap>): CellMap {
  const own = Object.fromEntries(references.filter((reference) => !reference.includes('!')).map((cell) => [cell, 0]))
  const sheets: Record<string, CellMap> = { ...all }
  for (const reference of references.filter((entry) => entry.includes('!'))) {
    const [name, cell] = reference.split('!') as [string, string]
    sheets[name] = { ...sheets[name], [cell]: 0 }
  }
  const inputs = sheet.definition.layout === 'list' ? { ...defaultInputs(sheet.definition), ...(golden.eingaben as CellMap) } : caseInputs(sheet, golden)
  return sheet.compute({ ...inputs, ...own }, createContext({ sheets }))
}

/**
 * Eine Abweichung ist nur begründet, wenn (1) die Webfassung keinen Wert zeigt,
 * (2) das Blatt sie für diese Zelle führt und eine der genannten Eingaben leer
 * ist und (3) die Gegenprobe stimmt: Mit 0 statt der leeren Eingaben liefert der
 * Rechenkern genau den Wert der Vorlage. So bleibt ein echter Rechenfehler, der
 * eine Zelle zusätzlich leert, nicht unentdeckt.
 */
function explain(sheet: AvailableSheet, golden: GoldenCase, mismatch: Mismatch, all: Record<string, CellMap>): Deviation | undefined {
  if (mismatch.actual !== null) return undefined
  const own = all[sheet.id] ?? {}
  const entries = sheet.deviations.filter((entry) => entry.cell === mismatch.cell && entry.whenEmpty.some((cell) => isEmptyReference(cell, own, all)))
  const first = entries[0]
  if (!first || entries.some((entry) => entry.check === 'none')) return first
  const empty = [...new Set(entries.flatMap((entry) => entry.whenEmpty.filter((cell) => isEmptyReference(cell, own, all))))]
  return sameValue(mismatch.expected, withZeros(sheet, golden, empty, all)[mismatch.cell] ?? null, isIntegerCell(sheet, mismatch.cell)) ? first : undefined
}

/** Ergebnisse aller Blätter des Falls (Verknüpfungen aus anderen Blättern eingeschlossen). */
export function caseWorkspace(sheet: AvailableSheet, golden: GoldenCase): Record<string, CellMap> {
  // Listenblätter (Blatt 17): ein Fall ist eine Stichprobeneinheit.
  if (sheet.definition.layout === 'list') return { [sheet.id]: sheet.compute({ ...defaultInputs(sheet.definition), ...(golden.eingaben as CellMap) }, createContext()) }
  return computeWorkspace(caseState(sheet, golden))
}

/** Ergebnisse des Blatts im Zusammenhang des ganzen Arbeitsstands. */
export function caseResults(sheet: AvailableSheet, golden: GoldenCase): CellMap {
  return caseWorkspace(sheet, golden)[sheet.id] ?? {}
}

export function compareCase(sheet: AvailableSheet, golden: GoldenCase): CaseReport {
  const all = caseWorkspace(sheet, golden)
  const results = all[sheet.id] ?? {}
  const report: CaseReport = { name: golden.name, compared: 0, explained: [], unexplained: [] }
  for (const [reference, expected] of Object.entries(golden.erwartet)) {
    const [name, cell] = reference.split('!') as [string, string]
    if (name !== sheet.id) continue
    report.compared += 1
    const actual = results[cell] ?? null
    if (sameValue(expected, actual, isIntegerCell(sheet, cell))) continue
    const mismatch = { cell, expected, actual }
    const deviation = explain(sheet, golden, mismatch, all)
    if (deviation) report.explained.push({ ...mismatch, deviation })
    else report.unexplained.push(mismatch)
  }
  return report
}
