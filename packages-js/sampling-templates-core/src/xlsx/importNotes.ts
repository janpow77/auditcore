/**
 * Hinweise zum Import der ausgefüllten Vorlage, die sich nicht auf einen
 * einzelnen umgedeuteten Wert beziehen: Daten außerhalb der gelesenen
 * Schichtspalten, ein in Blatt 18 nicht gewähltes Methodenblatt, gelöschte
 * Vorgaben und Kopien des Blatts 17 unter freiem Namen. Nichts davon wird
 * stillschweigend übergangen.
 */
import { isBlank } from '../excel/index'
import { inputFields, rowNumber, strataColumnsOf } from '../model/definition'
import type { AvailableSheet } from '../model/sheet'
import type { CellAddress, SheetId } from '../model/types'
import type { WorkbookCellValue } from './reader'

export type ImportNoteKind =
  /** Zahlen in Schichtzeilen außerhalb der gelesenen Schichtspalten (z. B. eine selbst angelegte Spalte K); sie werden nicht gelesen. */
  | 'unread-cells'
  /** In Blatt 18 der Mappe ist kein Methodenblatt gewählt; die Webfassung nimmt ein ausgefülltes Verfahren als aktiv an. */
  | 'method-not-chosen'
  /** Vorgabe der Vorlage in der Mappe gelöscht; die Webfassung übernimmt die leere Zelle (keine Vorgabe). */
  | 'default-cleared'
  /** Blatt mit freiem Namen als Kopie des Listenblatts (Blatt 17) erkannt und als Einheit gelesen. */
  | 'list-copy'

export interface ImportNote {
  kind: ImportNoteKind
  sheet: SheetId
  /** Betroffene Zellen bzw. der Name des Blatts in der Mappe. */
  detail: string
}

/** Spalte der Ergebnisübersicht der Verfahrensblätter (N3–N11); sie trägt Formeln der Vorlage, keine Schichtdaten. */
const SUMMARY_COLUMN = 'N'
/** Letzte Spalte, bis zu der nach ungelesenen Schichtdaten gesucht wird. */
const LAST_SCANNED_COLUMN = 26

function columnIndex(column: string): number {
  let index = 0
  for (const letter of column) index = index * 26 + (letter.charCodeAt(0) - 64)
  return index
}

/**
 * Zahlen in den Schichtzeilen eines Blatts, die rechts der sieben Schichtspalten
 * der Vorlage stehen (bis Spalte Z) und die die Webfassung nicht liest. Die
 * Fundstellen der Vorlage in diesen Spalten sind Text und zählen nicht.
 */
export function unreadStrataCells(sheet: AvailableSheet, cells: ReadonlyMap<string, WorkbookCellValue>): CellAddress[] {
  const columns = strataColumnsOf(sheet.definition)
  if (columns.length === 0) return []
  const read = new Set(columns)
  const first = columnIndex(columns[0] ?? 'D')
  const rows = new Set(inputFields(sheet.definition).filter((field) => field.columns).map((field) => rowNumber(field.cell)))
  const found: CellAddress[] = []
  for (const [address, cell] of cells) {
    const column = address.replace(/\d+$/, '')
    const index = columnIndex(column)
    if (!rows.has(rowNumber(address)) || read.has(column) || column === SUMMARY_COLUMN || index <= first || index > LAST_SCANNED_COLUMN) continue
    if (typeof cell.value === 'number') found.push(address)
  }
  return found
}

/** Zellen mit einer Vorgabe der Vorlage, die in der Mappe leer sind. */
export function clearedDefaults(sheet: AvailableSheet, cells: ReadonlyMap<string, WorkbookCellValue>): CellAddress[] {
  return inputFields(sheet.definition)
    .filter((field) => !field.web && !field.columns && field.default !== undefined && field.default !== null && isBlank(cells.get(field.cell)?.value))
    .map((field) => field.cell)
}

/** Zelle mit dem Titel eines Blatts; an ihr wird eine Kopie des Listenblatts unter freiem Namen erkannt. */
const TITLE_CELL = 'A1'

/** Blätter der Mappe, die denselben Titel tragen wie das Listenblatt, aber anders heißen. */
export function listCopies(sheet: AvailableSheet, names: readonly string[], cellsOf: (name: string) => ReadonlyMap<string, WorkbookCellValue>, known: ReadonlySet<string>): string[] {
  const title = cellsOf(sheet.id).get(TITLE_CELL)?.value
  if (typeof title !== 'string' || title === '') return []
  return names.filter((name) => name !== sheet.id && !known.has(name) && cellsOf(name).get(TITLE_CELL)?.value === title)
}
