/**
 * Stille Lücken: Eingaben, die fehlen, ohne dass die Vorlage es zeigt. Sie
 * rechnet dann ohne die Schicht, den Zeitraum oder die Größe weiter, und das
 * Ergebnis sieht vollständig aus. Die Webfassung rechnet genauso, weist die
 * Eingabe aber aus: Ein gezeigtes Ergebnis, das von einer leeren, nicht
 * freiwilligen Eingabe abhängt, trägt einen Hinweis in Warnfarbe.
 *
 * Ob das Ergebnis von einer leeren Eingabe abhängt, wird nachgerechnet: Das
 * Blatt wird mit einem Probewert an ihrer Stelle noch einmal gerechnet; ändert
 * sich eine Ergebniszelle, hängt sie davon ab. An den gezeigten Werten ändert
 * das nichts.
 */
import { isBlank, isNumber } from '../excel/index'
import { cellsOf, inputFields, rowNumber, strataColumnsOf, type FieldDefinition } from './definition'
import { SUMMARY_CELLS, type AvailableSheet } from './sheet'
import type { CellAddress, CellMap, CellValue, SheetContext } from './types'

/** Relative Abweichung, ab der zwei Ergebnisse als verschieden gelten. */
const TOLERANCE = 1e-12

/**
 * Zellen, an denen das Ergebnis des Blatts hängt: extrapolierter Fehler und
 * Fehlerquote der Ergebnisübersicht und die Größen der Skala; bei Blättern ohne
 * Skala (Blatt 02, Bericht) die Größen ihrer Ergebnisspalte.
 */
export function resultCellsOf(sheet: AvailableSheet): CellAddress[] {
  const { gauge, primary, rows } = sheet.definition.summary
  const cells = gauge ? [SUMMARY_CELLS.projectedError, SUMMARY_CELLS.totalErrorRate, gauge.rate, gauge.upper] : [primary.cell, ...rows.map((row) => row.cell)]
  return [...new Set(cells.filter((cell): cell is string => cell !== undefined))]
}

/** Zellen, an denen eine stille Lücke gemessen wird: die Ergebniszellen und die Hauptgröße (bei Verfahrensblättern der Stichprobenumfang). */
function watchedCells(sheet: AvailableSheet): CellAddress[] {
  return [...new Set([...resultCellsOf(sheet), sheet.definition.summary.primary.cell])]
}

/** Für sich freiwillige Eingaben der Verfahrensblätter: Leer heißt „keine“ bzw. „Wert der Planung“. */
const OPTIONAL_ALONE = /^(systemicErrors|anomalousErrors|(updated|final)AnticipatedErrorRate)$/
/** Freiwillige Gruppen der Verfahrensblätter je Zeitraum: hochwertige Einheiten und umfassende Schicht. */
const OPTIONAL_GROUPS: readonly (readonly [RegExp, string])[] = [
  [/^(?:stratumH|ppsH|h)ighValue(?:Units|BookValue|Errors)(Period\d)?$/, 'highValue'],
  [/^exhaustive(?:BookValue|Units|HighValueUnits|Errors)(Period\d)?$/, 'exhaustive'],
]

/**
 * Freiwilligkeit eines Felds: die Angabe der Definition (`optional`), sonst nach
 * dem Namen des Felds – die Verfahrensblätter benennen gleiche Größen gleich.
 */
export function optionalOf(field: FieldDefinition): true | string | undefined {
  if (field.optional !== undefined) return field.optional
  if (OPTIONAL_ALONE.test(field.alias)) return true
  for (const [pattern, name] of OPTIONAL_GROUPS) {
    const match = pattern.exec(field.alias)
    if (match) return `${name}${match[1] ?? ''}`
  }
  return undefined
}

function differs(left: CellValue | undefined, right: CellValue | undefined): boolean {
  if (isNumber(left) && isNumber(right)) return Math.abs(left - right) > TOLERANCE * Math.max(1, Math.abs(left))
  return (left ?? null) !== (right ?? null)
}

/**
 * Probewerte für eine leere Eingabe: bei Auswahlfeldern jede Auswahl, sonst
 * Zahlen verschiedener Größenordnung – bei Beträgen und Anzahlen auch eine über
 * allen eingetragenen Werten (`large`), weil manche Formel erst oberhalb einer
 * anderen Größe reagiert (Erhöhung nur, wenn der Ist-Wert die Prognose übersteigt).
 */
function probesOf(field: FieldDefinition, context: SheetContext, large: number): CellValue[] {
  if (field.options) return [...field.options]
  if (field.list === 'confidence') return context.parameters.zTable.map((row) => row.confidence)
  if (field.list) return [...context.parameters.lists[field.list]]
  return field.type === 'percent' || field.type === 'decimal' ? [0.07, 0.31, 0.97] : [7, 31, large]
}

/** Zahl über allen eingetragenen Beträgen und Anzahlen des Blatts. */
function largeProbe(sheet: AvailableSheet, cells: CellMap): number {
  const values = inputFields(sheet.definition).flatMap((field) => cellsOf(field).map((cell) => cells[cell])).filter(isNumber)
  return 10 * Math.max(1000, ...values.map((value) => Math.abs(value)))
}

/** Schichtspalten mit irgendeiner Eingabe. */
function usedColumns(sheet: AvailableSheet, cells: CellMap): Set<string> {
  const rows = inputFields(sheet.definition).filter((field) => field.columns).map((field) => rowNumber(field.cell))
  return new Set(strataColumnsOf(sheet.definition).filter((column) => rows.some((row) => !isBlank(cells[`${column}${row}`]))))
}

/** Freiwillige Eingabe: allein freiwillig oder Teil einer Gruppe, von der (in derselben Schicht) nichts eingetragen ist. */
function isOptional(sheet: AvailableSheet, field: FieldDefinition, cell: CellAddress, cells: CellMap): boolean {
  const optional = optionalOf(field)
  if (optional === undefined || optional === true) return optional === true
  const column = field.columns ? cell.replace(/\d+$/, '') : undefined
  const group = inputFields(sheet.definition).filter((other) => optionalOf(other) === optional)
  return group.every((other) => isBlank(cells[other.columns && column ? `${column}${rowNumber(other.cell)}` : other.cell]))
}

/** Leere, nicht freiwillige Eingaben des Blatts; bei Schichtzeilen nur die belegter Schichten. */
function candidates(sheet: AvailableSheet, cells: CellMap): { field: FieldDefinition; cell: CellAddress }[] {
  const used = usedColumns(sheet, cells)
  return inputFields(sheet.definition)
    .filter((field) => !field.web && field.type !== 'text')
    .flatMap((field) => cellsOf(field).map((cell) => ({ field, cell })))
    .filter(({ field, cell }) => isBlank(cells[cell]) && (!field.columns || used.has(cell.replace(/\d+$/, ''))) && !isOptional(sheet, field, cell, cells))
}

/**
 * Leere Eingaben, von denen ein gezeigtes Ergebnis abhängt. `base` sind die
 * Zellwerte des Rechenkerns zu `inputs`; `skip` nennt Eingaben, die schon
 * anderweitig ausgewiesen sind („mit 0 berechnet“).
 */
export function silentInputs(sheet: AvailableSheet, inputs: CellMap, base: CellMap, context: SheetContext, skip: ReadonlySet<CellAddress> = new Set()): CellAddress[] {
  const results = watchedCells(sheet).filter((cell) => isNumber(base[cell]))
  if (results.length === 0) return []
  const large = largeProbe(sheet, base)
  const depends = (field: FieldDefinition, cell: CellAddress): boolean =>
    probesOf(field, context, large).some((probe) => {
      const run = sheet.compute({ ...inputs, [cell]: probe }, context)
      return results.some((result) => differs(base[result], run[result]))
    })
  return candidates(sheet, base)
    .filter(({ cell }) => !skip.has(cell))
    .filter(({ field, cell }) => depends(field, cell))
    .map(({ cell }) => cell)
}
