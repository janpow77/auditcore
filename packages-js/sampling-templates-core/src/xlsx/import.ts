/**
 * Excel-Dateien öffnen: den Export dieser Anwendung (Arbeitsstand im Blatt
 * `_Arbeitsstand`) und die ausgefüllte Originalvorlage. Aus der Vorlage werden
 * die Eingabe- und Verknüpfungszellen aller Blätter mit Rechenkern gelesen.
 * Nichts wird stillschweigend verworfen oder umgedeutet: Jeder solche Wert
 * steht mit Blatt, Zelle, gefundenem Wert und Grund in `issues`.
 */
import { parseDecimal } from '@auditcore/common'
import { eq, isBlank, isNumber, sameText } from '../excel/index'
import { fieldOptions } from '../format/numbers'
import { cellsOf, defaultInputs, fieldsOf, inputFields, type FieldDefinition } from '../model/definition'
import { SUMMARY_CELLS, createContext, type AvailableSheet, type SheetModule } from '../model/sheet'
import type { CellAddress, CellMap, CellValue, Parameters, SheetId } from '../model/types'
import { TEMPLATE_STRATA } from '../model/strata'
import { SHEETS } from '../sheets/registry'
import { WORKSPACE_SHEET } from './export'
import { clearedDefaults, listCopies, unreadStrataCells, type ImportNote } from './importNotes'
import { readWorkbook, type ReadWorkbook, type WorkbookCellValue } from './reader'

/** Warum ein Wert der Mappe nicht unverändert übernommen wurde. */
export type ImportReason =
  /** Auswahlwert in anderer Schreibweise; dem Listeneintrag zugeordnet. */
  | 'normalized'
  /** Zahl stand als Text in der Zelle; als Zahl gelesen. */
  | 'number-from-text'
  /** Zelle trägt eine eigene Formel; ihr berechneter Wert wurde übernommen. */
  | 'formula-value'
  /** Zahl in einem Textfeld; als Text übernommen. */
  | 'number-as-text'
  /** Datum als laufende Tageszahl der Tabellenkalkulation; als Datum `TT.MM.JJJJ` übernommen. */
  | 'date-from-serial'
  /** Wert steht nicht in der Auswahlliste; nicht übernommen. */
  | 'not-in-list'
  /** Keine lesbare Zahl; nicht übernommen. */
  | 'not-a-number'
  /** Wahrheitswert oder Fehlerwert; nicht übernommen. */
  | 'unsupported'

/** Ein Wert der Mappe, der umgedeutet oder nicht übernommen wurde. */
export interface ImportIssue {
  sheet: SheetId
  cell: CellAddress
  /** Bezeichnung des Felds. */
  label: string
  /** Wert, wie er in der Mappe steht. */
  found: string
  reason: ImportReason
  /** Übernommener Wert; `null`: nicht übernommen. */
  used: CellValue
}

export type WorkbookImport =
  /** Export dieser Anwendung: Text der Arbeitsstandsdatei, weiter mit `openWorkspace`. */
  | { kind: 'workspace'; text: string }
  /** Ausgefüllte Originalvorlage. */
  | {
      kind: 'template'
      /** Eingaben je Blatt mit Rechenkern (Listenblatt: eine Einheit). */
      sheets: Record<SheetId, CellMap | readonly CellMap[]>
      /** Blätter, die mehr als die Vorgaben der Vorlage enthalten. */
      filled: readonly SheetId[]
      /** Blätter der Vorlage ohne Rechenkern; sie werden noch nicht gelesen. */
      pending: readonly SheetId[]
      /** Umgedeutete und nicht übernommene Werte. */
      issues: readonly ImportIssue[]
      /** Weitere Hinweise: ungelesene Schichtdaten, kein Methodenblatt gewählt, gelöschte Vorgaben, Kopien des Blatts 17. */
      notes: readonly ImportNote[]
      /** Zuletzt berechnete Werte der Formelzellen der Mappe, für den Vergleich mit der Webfassung. */
      cached: Record<SheetId, CellMap>
      /** In Blatt 18 der Mappe gewähltes Methodenblatt (Zelle C4), wenn es ein Blatt mit Rechenkern nennt. */
      method: SheetId | null
    }
  /** Weder Arbeitsstand noch Blätter der Vorlage. */
  | { kind: 'unknown' }

type Read = { value: CellValue; reason?: ImportReason }

function workspaceText(workbook: ReadWorkbook): string {
  const cells = workbook.cells(WORKSPACE_SHEET)
  let text = ''
  for (let row = 1; cells.has(`A${row}`); row += 1) text += String(cells.get(`A${row}`)?.value ?? '')
  return text
}

/** Zahl aus einem Text der Mappe: deutsche und englische Schreibweise, Prozentzeichen als Anteil. */
function numberFromText(text: string): number | null {
  const percent = text.includes('%')
  const parsed = parseDecimal(text.replace(/%/g, ' '), { mode: 'auto', maxFractionDigits: 15 })
  if (parsed === null) return null
  return percent ? parsed / 100 : parsed
}

/** Auswahlwert dem Listeneintrag zuordnen: gleiche Schreibweise, sonst ohne Groß-/Kleinschreibung und Leerraum, Zahlen auch als Text. */
function readChoice(field: FieldDefinition, raw: number | string, parameters: Parameters): Read {
  const options = fieldOptions(field, parameters).map((option) => option.value)
  if (options.includes(raw)) return { value: raw }
  const number = typeof raw === 'number' ? raw : numberFromText(raw)
  const match = options.find((option) => (typeof option === 'number' ? number !== null && eq(option, number) : sameText(String(raw).trim(), option)))
  return match === undefined ? { value: null, reason: 'not-in-list' } : { value: match, reason: 'normalized' }
}

function readNumber(raw: number | string): Read {
  if (isNumber(raw)) return { value: raw }
  const number = numberFromText(String(raw))
  return number === null ? { value: null, reason: 'not-a-number' } : { value: number, reason: 'number-from-text' }
}

/** Wert passend zum Feld lesen. */
function readValue(field: FieldDefinition, raw: number | string, parameters: Parameters): Read {
  if (field.list || field.options) return readChoice(field, raw, parameters)
  if (field.type === 'text') return typeof raw === 'number' ? readNumberInText(field, raw) : { value: raw }
  return readNumber(raw)
}

/** Tag 0 der Tabellenkalkulation (30.12.1899). */
const SERIAL_EPOCH = Date.UTC(1899, 11, 30)
const DAY = 86400000

/** Zahl in einem Textfeld: Trägt das Feld ein Datumsformat, ist sie die laufende Tageszahl eines Datums. */
function readNumberInText(field: FieldDefinition, raw: number): Read {
  if (!/yyyy/i.test(field.format ?? '')) return { value: String(raw), reason: 'number-as-text' }
  const date = new Date(SERIAL_EPOCH + Math.round(raw) * DAY)
  const two = (value: number): string => String(value).padStart(2, '0')
  return { value: `${two(date.getUTCDate())}.${two(date.getUTCMonth() + 1)}.${date.getUTCFullYear()}`, reason: 'date-from-serial' }
}

/** Trägt die Verknüpfungszelle noch die Formel der Vorlage (`='02_Grundgesamtheit'!$C$51`)? */
function isUntouchedLink(field: FieldDefinition, cell: WorkbookCellValue): boolean {
  if (!field.link || !cell.formula) return false
  const formula = cell.formulaText.replace(/^=/, '').replace(/[$']/g, '').trim()
  return formula === `${field.link.sheet}!${field.link.cell}`
}

class TemplateReader {
  readonly issues: ImportIssue[] = []

  constructor(
    private readonly workbook: ReadWorkbook,
    private readonly parameters: Parameters,
  ) {}

  private report(sheet: AvailableSheet, field: FieldDefinition, cell: CellAddress, found: unknown, reason: ImportReason, used: CellValue): void {
    this.issues.push({ sheet: sheet.id, cell, label: field.label, found: String(found), reason, used })
  }

  /** Eingabe einer Zelle oder `null`; jede Umdeutung und jeder nicht übernommene Wert wird gemeldet. */
  private input(sheet: AvailableSheet, field: FieldDefinition, address: CellAddress, cell: WorkbookCellValue | undefined): CellValue {
    if (!cell || isUntouchedLink(field, cell)) return null
    const raw = cell.value
    if (isBlank(raw)) return null
    if (typeof raw === 'boolean') {
      this.report(sheet, field, address, raw, 'unsupported', null)
      return null
    }
    const read = readValue(field, raw, this.parameters)
    if (read.reason) this.report(sheet, field, address, raw, read.reason, read.value)
    else if (cell.formula) this.report(sheet, field, address, `=${cell.formulaText.replace(/^=/, '')}`, 'formula-value', read.value)
    return read.value
  }

  /** `name`: Blattname in der Mappe (bei Kopien des Listenblatts abweichend vom Blatt der Vorlage). */
  sheet(sheet: AvailableSheet, name: string = sheet.id): { inputs: CellMap; filled: boolean; cached: CellMap } {
    const cells = this.workbook.cells(name)
    const inputs: Record<string, CellValue> = {}
    let filled = false
    for (const field of inputFields(sheet.definition).filter((entry) => !entry.web)) {
      for (const address of cellsOf(field)) {
        const value = this.input(sheet, field, address, cells.get(address))
        if (value === null) continue
        inputs[address] = value
        if (value !== (field.default ?? null)) filled = true
      }
    }
    return { inputs, filled, cached: cachedResults(sheet, cells) }
  }

  /**
   * Blattweite Hinweise und gelöschte Vorgaben: Ist das Blatt ausgefüllt und eine
   * Vorgabe der Vorlage in der Mappe leer, übernimmt die Webfassung die leere
   * Zelle (`null`), statt die Vorgabe wieder einzusetzen – so rechnet sie wie die Mappe.
   */
  notes(sheet: AvailableSheet, filled: boolean, name: string = sheet.id): { notes: ImportNote[]; cleared: CellMap } {
    const cells = this.workbook.cells(name)
    // Nur für ausgefüllte Blätter: Ein unberührtes Blatt der Vorlage trägt nichts, was verloren gehen könnte.
    const unread = filled ? unreadStrataCells(sheet, cells) : []
    const cleared = filled ? clearedDefaults(sheet, cells) : []
    return {
      notes: [
        ...(unread.length ? [{ kind: 'unread-cells' as const, sheet: sheet.id, detail: unread.join(', ') }] : []),
        ...(cleared.length ? [{ kind: 'default-cleared' as const, sheet: sheet.id, detail: cleared.join(', ') }] : []),
      ],
      cleared: Object.fromEntries(cleared.map((cell) => [cell, null])),
    }
  }
}

/**
 * Zuletzt berechnete Werte der Formel- und Ergebniszellen eines Blatts der Mappe.
 * Trägt das Blatt Formeln, aber keine einzige mit einem Rechenwert, ist die Datei
 * nie berechnet worden (z. B. von einem Programm ohne Rechenkern geschrieben):
 * Dann gibt es nichts zu vergleichen, und alle Werte sind `null`. Die Zelle mit
 * dem gewählten Methodenblatt in Blatt 18 ist in der Mappe eine Eingabe und zählt nicht mit.
 */
function cachedResults(sheet: AvailableSheet, cells: ReadonlyMap<string, WorkbookCellValue>): CellMap {
  const cached: Record<string, CellValue> = {}
  const formulas = [...cells.values()].filter((cell) => cell.formula)
  const neverComputed = formulas.length > 0 && formulas.every((cell) => isBlank(cell.value))
  for (const address of comparedCells(sheet, cells)) {
    const value = cells.get(address)?.value
    cached[address] = neverComputed || typeof value === 'boolean' || value === undefined || value === '' ? null : value
  }
  return cached
}

/**
 * Zellen des Blatts, die mit der Mappe verglichen werden: Formel- und
 * Ergebniszellen (Schichtzeilen nur in den sieben Spalten der Vorlage, dazu die
 * Summenzelle) und bei Verfahrensblättern die Ergebnisübersicht N3–N11, aus der
 * Blatt 18 liest. Zellen, die es in der Mappe nicht gibt, entfallen – „Mappe
 * leer“ heißt: Die Formel der Mappe ergibt nichts.
 */
function comparedCells(sheet: AvailableSheet, cells: ReadonlyMap<string, WorkbookCellValue>): CellAddress[] {
  const computed = fieldsOf(sheet.definition).filter((field) => !field.web && (field.kind === 'formula' || field.kind === 'result'))
  const summary = sheet.definition.summary.gauge && cells.has(SUMMARY_CELLS.method) ? Object.values(SUMMARY_CELLS) : []
  const templateCells = (field: FieldDefinition): CellAddress[] => (field.columns ? cellsOf(field).slice(0, TEMPLATE_STRATA.length) : cellsOf(field))
  const chosen = (address: CellAddress): boolean => sheet.id === TOTAL_ERROR_RATE_SHEET && address === METHOD_CELL
  return [...computed.flatMap((field) => [...templateCells(field), ...(field.total ? [field.total] : [])]), ...summary].filter((address) => cells.has(address) && !chosen(address))
}

/** Blatt 18 der Vorlage und die Zelle, in der das Methodenblatt gewählt wird. */
const TOTAL_ERROR_RATE_SHEET = '18_GFQ_AnhIII'
const METHOD_CELL = 'C4'

/** In der Mappe gewähltes Methodenblatt, sofern es ein Blatt mit Rechenkern ist. */
function chosenMethod(workbook: ReadWorkbook, sheets: readonly SheetModule[]): SheetId | null {
  if (!workbook.sheetNames.includes(TOTAL_ERROR_RATE_SHEET)) return null
  const chosen = workbook.cells(TOTAL_ERROR_RATE_SHEET).get(METHOD_CELL)?.value
  return typeof chosen === 'string' && sheets.some((sheet) => sheet.available && sheet.id === chosen) ? chosen : null
}

/**
 * Einheiten eines Listenblatts: das Blatt selbst und seine Kopien in der Mappe
 * (die Vorlage wird je Stichprobeneinheit kopiert, die Kopien heißen dann z. B.
 * `17_Unterstichprobe (2)`). Vorgaben der Webfelder kommen dazu.
 */
function listUnits(reader: TemplateReader, workbook: ReadWorkbook, sheet: AvailableSheet, known: ReadonlySet<string>): { rows: CellMap[]; cached: CellMap; notes: ImportNote[] } {
  const numbered = workbook.sheetNames.filter((name) => name === sheet.id || name.startsWith(`${sheet.id} `) || name.startsWith(`${sheet.id}_`) || name.startsWith(`${sheet.id}(`))
  // Kopien unter freiem Namen: am Titel des Blatts erkannt und genannt.
  const copies = listCopies(sheet, workbook.sheetNames, (name) => workbook.cells(name), new Set([...known, ...numbered]))
  const rows: CellMap[] = []
  let cached: CellMap = {}
  for (const name of [...numbered, ...copies]) {
    const read = reader.sheet(sheet, name)
    if (name === sheet.id) cached = read.cached
    if (read.filled) rows.push({ ...defaultInputs(sheet.definition), ...read.inputs })
  }
  return { rows, cached, notes: copies.map((name) => ({ kind: 'list-copy' as const, sheet: sheet.id, detail: name })) }
}

/**
 * Liest eine `.xlsx`-Datei: alle Blätter der Vorlage mit Rechenkern. `filled`
 * nennt die Blätter, die mehr als die Vorgaben enthielten – Blatt 18 auch dann,
 * wenn dort nur das Methodenblatt gewählt ist; Blätter ohne Rechenkern stehen
 * unter `pending` und werden nicht gelesen.
 */
export function importWorkbook(data: Uint8Array | ArrayBuffer, sheets: readonly SheetModule[] = SHEETS): WorkbookImport {
  const workbook = readWorkbook(data instanceof Uint8Array ? data : new Uint8Array(data))
  if (workbook.sheetNames.includes(WORKSPACE_SHEET)) return { kind: 'workspace', text: workspaceText(workbook) }
  const present = sheets.filter((sheet) => workbook.sheetNames.includes(sheet.id))
  if (present.length === 0) return { kind: 'unknown' }
  const reader = new TemplateReader(workbook, createContext().parameters)
  const method = chosenMethod(workbook, sheets)
  const result: Collected = { inputs: {}, cached: {}, filled: [], notes: [] }
  const known = new Set(sheets.map((sheet) => sheet.id))
  for (const sheet of present.filter(isAvailable)) {
    if (sheet.definition.layout === 'list') collectList(result, reader, workbook, sheet, known)
    else collectSheet(result, reader, sheet, sheet.id === TOTAL_ERROR_RATE_SHEET && method !== null)
  }
  if (method === null && methodMissing(workbook, result.filled, sheets)) result.notes.push({ kind: 'method-not-chosen', sheet: TOTAL_ERROR_RATE_SHEET, detail: METHOD_CELL })
  // Blätter ohne Rechenkern; Nachschlagetabellen (X1a) enthalten keine Eingaben und zählen nicht dazu.
  const pending = present.filter((sheet) => !sheet.available && !sheet.table).map((sheet) => sheet.id)
  return { kind: 'template', sheets: result.inputs, filled: result.filled, pending, issues: reader.issues, notes: result.notes, cached: result.cached, method }
}

interface Collected {
  inputs: Record<SheetId, CellMap | readonly CellMap[]>
  cached: Record<SheetId, CellMap>
  filled: SheetId[]
  notes: ImportNote[]
}

const isAvailable = (sheet: SheetModule): sheet is AvailableSheet => sheet.available

/**
 * Kein Methodenblatt in Blatt 18 gewählt, aber ein Verfahren ausgefüllt: Die
 * Webfassung nimmt eines als aktiv an und zeigt in Blatt 18 Werte, wo die Mappe leer ist.
 */
function methodMissing(workbook: ReadWorkbook, filled: readonly SheetId[], sheets: readonly SheetModule[]): boolean {
  return workbook.sheetNames.includes(TOTAL_ERROR_RATE_SHEET) && filled.some((id) => isMethodSheet(id, sheets))
}

/** Verfahrensblatt: ein Blatt mit Ergebnisübersicht (Skala), ausgenommen Blatt 18 selbst. */
function isMethodSheet(id: SheetId, sheets: readonly SheetModule[]): boolean {
  const sheet = sheets.find((entry) => entry.id === id)
  return sheet !== undefined && sheet.available && sheet.definition.summary.gauge !== undefined && id !== TOTAL_ERROR_RATE_SHEET
}

function collectList(result: Collected, reader: TemplateReader, workbook: ReadWorkbook, sheet: AvailableSheet, known: ReadonlySet<string>): void {
  const units = listUnits(reader, workbook, sheet, known)
  result.inputs[sheet.id] = units.rows
  result.cached[sheet.id] = units.cached
  result.notes.push(...units.notes)
  if (units.rows.length > 0) result.filled.push(sheet.id)
}

/** `chosen`: Das Blatt gilt auch ohne eigene Eingabe als ausgefüllt (Blatt 18 mit gewähltem Methodenblatt). */
function collectSheet(result: Collected, reader: TemplateReader, sheet: AvailableSheet, chosen: boolean): void {
  const read = reader.sheet(sheet)
  const filled = read.filled || chosen
  const extra = reader.notes(sheet, filled)
  result.inputs[sheet.id] = { ...read.inputs, ...extra.cleared }
  result.cached[sheet.id] = read.cached
  result.notes.push(...extra.notes)
  if (filled) result.filled.push(sheet.id)
}
