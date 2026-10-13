/**
 * Abgleich eines Rechenkerns mit den Golden-Dateien: jede Formelzelle des
 * Blatts mit relativer Toleranz 1e-9, Texte wortgleich. Eine Abweichung ist nur
 * zulässig, wenn das Blatt sie als begründete Abweichung führt (`deviations`).
 */
import { readFileSync, readdirSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { isNumber } from '../src/excel/index'
import { defaultInputs, findField } from '../src/model/definition'
import { evaluateSheet } from '../src/model/evaluate'
import { TEMPLATE_POLICY } from '../src/model/policy'
import { SUMMARY_CELLS, createContext, isEmptyReference, type AvailableSheet, type SheetModule } from '../src/model/sheet'
import type { CellMap, CellValue, Deviation, MissingPolicy } from '../src/model/types'
import { SHEETS, availableSheets } from '../src/sheets/registry'
import { computeWorkspace, contextFor } from '../src/workspace/compute'
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
  // Blatt 18 und 20: Das Methodenblatt aus Zelle C4 des Blatts 18 ist in der Webfassung das aktive Verfahren, keine Eingabe.
  const choice = METHOD_CHOICE[sheet.id]
  for (const [reference, value] of Object.entries(golden.eingaben)) {
    if (reference === choice) continue
    const [name, cell] = reference.includes('!') ? (reference.split('!') as [string, string]) : [sheet.id, reference]
    const target = inputs[name]
    if (target) target[cell] = value
  }
  return { ...emptyWorkspace(), activeMethod: choice ? chosenMethod(golden, choice) : sheet.id, sheets: inputs }
}

/**
 * Blätter, die die Ergebnisübersicht des aktiven Verfahrens lesen, mit der Eingabe
 * des Falls, die das Methodenblatt nennt (in der Vorlage `18_GFQ_AnhIII!C4`).
 */
const METHOD_CHOICE: Readonly<Record<string, string>> = { '18_GFQ_AnhIII': 'C4', '20_Druck_KOM': '18_GFQ_AnhIII!C4' }

/** Im Fall gewähltes Methodenblatt; ohne Angabe ist kein Verfahren aktiv. */
function chosenMethod(golden: GoldenCase, choice: string): string | null {
  const value = golden.eingaben[choice]
  return typeof value === 'string' && value !== '' ? value : null
}

/** Kontext der Gegenproben: für die Blätter 18 und 20 mit der Ergebnisübersicht des aktiven Verfahrens, sonst wie bisher. */
function checkContext(sheet: AvailableSheet, golden: GoldenCase, sheets: Record<string, CellMap>, policy?: MissingPolicy) {
  return METHOD_CHOICE[sheet.id] ? contextFor(sheet.id, caseState(sheet, golden), sheets, policy) : createContext({ sheets, policy })
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
  return sheet.compute({ ...inputs, ...own }, checkContext(sheet, golden, sheets))
}

/** Rechnet das Blatt unter der Richtlinie „wie die Vorlage“ (`TEMPLATE_POLICY`). */
function likeTemplate(sheet: AvailableSheet, golden: GoldenCase, all: Record<string, CellMap>): CellMap {
  // Blatt 18 und 20 bauen auf Blatt 02 und dem Methodenblatt auf: Die Gegenprobe rechnet den ganzen Arbeitsstand wie die Vorlage.
  if (METHOD_CHOICE[sheet.id]) return caseWorkspace(sheet, golden, TEMPLATE_POLICY)[sheet.id] ?? {}
  const inputs = sheet.definition.layout === 'list' ? { ...defaultInputs(sheet.definition), ...(golden.eingaben as CellMap) } : caseInputs(sheet, golden)
  return evaluateSheet(sheet, inputs, createContext({ sheets: all, policy: TEMPLATE_POLICY })).cells
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
  const required = entries.filter((entry) => entry.kind !== 'withoutBasis')
  const unchecked = required.find((entry) => entry.check === 'none')
  if (unchecked) return unchecked
  if (required[0]) {
    const empty = [...new Set(required.flatMap((entry) => entry.whenEmpty.filter((cell) => isEmptyReference(cell, own, all))))]
    if (sameValue(mismatch.expected, withZeros(sheet, golden, empty, all)[mismatch.cell] ?? null, isIntegerCell(sheet, mismatch.cell))) return required[0]
  }
  // Prüfhinweis ohne Grundlage: Unter der Richtlinie „wie die Vorlage“ muss der Rechenkern genau den Wert der Vorlage liefern.
  const withoutBasis = entries.find((entry) => entry.kind === 'withoutBasis')
  return withoutBasis && sameValue(mismatch.expected, likeTemplate(sheet, golden, all)[mismatch.cell] ?? null) ? withoutBasis : undefined
}

/** Ergebnisse aller Blätter des Falls (Verknüpfungen aus anderen Blättern eingeschlossen). */
export function caseWorkspace(sheet: AvailableSheet, golden: GoldenCase, policy?: MissingPolicy): Record<string, CellMap> {
  // Listenblätter (Blatt 17): ein Fall ist eine Stichprobeneinheit.
  if (sheet.definition.layout === 'list') return { [sheet.id]: evaluateSheet(sheet, { ...defaultInputs(sheet.definition), ...(golden.eingaben as CellMap) }, createContext({ policy })).cells }
  return computeWorkspace(caseState(sheet, golden), involvedSheets(sheet, golden), policy)
}

/** Blatt, aus dem die Methodenblätter ihre Verknüpfungen beziehen. */
const POPULATION_SHEET = '02_Grundgesamtheit'

/**
 * Blätter, die für einen Fall gerechnet werden müssen: das Blatt selbst, Blatt 02
 * und jedes Blatt, in das der Fall Eingaben schreibt. Die übrigen Blätter tragen
 * nichts bei; sie mitzurechnen kostete nur Zeit.
 */
export function involvedSheets(sheet: AvailableSheet, golden: GoldenCase): SheetModule[] {
  const named = new Set([sheet.id, POPULATION_SHEET, ...Object.keys(golden.eingaben).filter((reference) => reference.includes('!')).map((reference) => reference.split('!')[0] as string)])
  // Blatt 18 und 20: zusätzlich das gewählte Methodenblatt und Blatt 18, auch wenn der Fall dort nichts einträgt.
  const choice = METHOD_CHOICE[sheet.id]
  if (choice) for (const id of [chosenMethod(golden, choice), '18_GFQ_AnhIII']) if (id) named.add(id)
  return SHEETS.filter((entry) => named.has(entry.id))
}

/** Zellen, in denen die Webfassung unter der Richtlinie „wie die Vorlage“ etwas anderes zeigt als die Vorlage – Soll: keine. */
export function templateMismatches(sheet: AvailableSheet, golden: GoldenCase): Mismatch[] {
  const results = caseWorkspace(sheet, golden, TEMPLATE_POLICY)[sheet.id] ?? {}
  const mismatches: Mismatch[] = []
  for (const [reference, expected] of Object.entries(golden.erwartet)) {
    const [name, cell] = reference.split('!') as [string, string]
    const actual = results[cell] ?? null
    if (name === sheet.id && !sameValue(expected, actual, isIntegerCell(sheet, cell))) mismatches.push({ cell, expected, actual })
  }
  return mismatches
}

/** `SAMPLING_TEMPLATES_SHEET=<Blatt>[,<Blatt>…]` beschränkt Abgleich und Abweichungstests auf diese Blätter. */
export function selectedSheets(): AvailableSheet[] {
  const only = (process.env.SAMPLING_TEMPLATES_SHEET ?? '').split(',').map((name) => name.trim()).filter(Boolean)
  return availableSheets().filter((sheet) => only.length === 0 || only.includes(sheet.id))
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
