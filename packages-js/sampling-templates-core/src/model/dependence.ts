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

/**
 * Freiwillige Eingaben nach der Original-Arbeitsmappe der Vorlage. Maßgeblich ist,
 * was die Vorlage selbst als freiwillig erkennen lässt; alles andere ist Pflicht,
 * sobald ein gezeigtes Ergebnis davon abhängt. Ausgewertet sind Bezeichnungen,
 * Kommentare, Datenüberprüfungen, bedingte Formatierungen, Farblegende und
 * Formeln (Tabelle in `docs/abweichungen.md`, Nr. 13):
 *
 * - **Gekennzeichnet** – „(leer = Wert aus I)“ bzw. „(leer = vorheriger Wert)“ an
 *   der aktualisierten voraussichtlichen Fehlerquote (05 B51, 06 B54, 07 B57/B93,
 *   10 B57, 11 B60, 12 B64/B100) und „(fakultativ)“ am Buchwert der umfassenden
 *   Schicht (08 B9, 09 B8, 10 B9/B51, 11 B7/B53, 12 B9/B55/B94, 13 B10, 14 B8,
 *   17 B8). Die übrigen Angaben dieser Schicht (Anzahl, davon hochwertige,
 *   Fehlersumme) teilen das als Gruppe: leer nur gemeinsam.
 * - **Ohne Kennzeichnung, Vorlage liest leer als 0** (`N(…)`) – nach
 *   Entscheidung des Inhabers vom 17.10.2026 freiwillig, leer heißt „keine“:
 *   abgegrenzte systembedingte und nicht berichtigte anomale Fehler; Anzahl,
 *   Buchwert und Fehler der hochwertigen Einheiten (Gruppe); die Einheiten der
 *   Zufallsschicht mit BV > Auswahlintervall (Iteration, z. B. 03 C35); in
 *   Blatt 02 TH-Pauschale, negative Datensätze, Ausschlüsse nach Art. 15 Abs. 5,
 *   Wiederaufnahmen und Art.-80-Einheiten; in Blatt 20 J6–J8 (Definitionen).
 *   Gruppen: Ist ein Teil gefüllt, sind die übrigen Pflicht.
 * - **Von keiner Formel verwendet** (Geschäftsjahr, Programm, Stichprobeneinheit,
 *   Schichtungskriterium, Freitexte; einzelne Zahlenfelder wie N in Blatt 03):
 *   freiwillig, weil kein Ergebnis davon abhängt – die Prüfung unten findet dort
 *   nie eine Abhängigkeit, Textfelder prüft sie gar nicht.
 *
 * Die Altvorlagen X1–X4 kennen keine dieser Kennzeichnungen und verwenden ihre
 * Eingaben unmittelbar; dort gilt keine Regel nach dem Feldnamen (`optional: false`).
 */
/** Für sich freiwillig. */
const OPTIONAL_ALONE = /^(systemicErrors|anomalousErrors|(updated|final)AnticipatedErrorRate|(stratumI|i)terationUnits(Period\d)?)$/
/** Freiwillige Gruppen je Zeitraum und Schicht: hochwertige Einheiten und umfassende Schicht. */
const OPTIONAL_GROUPS: readonly (readonly [RegExp, string])[] = [
  [/^(?:stratumH|ppsH|h)ighValue(?:Units|BookValue|Errors)(Period\d)?$/, 'highValue'],
  [/^exhaustive(?:BookValue|Units|HighValueUnits|Errors)(Period\d)?$/, 'exhaustive'],
]

/**
 * Freiwilligkeit eines Felds: die Angabe der Definition (`optional`; `false` heißt
 * Pflicht trotz des Namens), sonst nach dem Namen des Felds – die Verfahrensblätter
 * benennen gleiche Größen gleich.
 */
export function optionalOf(field: FieldDefinition): true | string | undefined {
  if (field.optional === false) return undefined
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
