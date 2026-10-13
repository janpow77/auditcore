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
import { createContext, type AvailableSheet, type SheetModule } from '../model/sheet'
import type { CellAddress, CellMap, CellValue, Parameters, SheetId } from '../model/types'
import { SHEETS } from '../sheets/registry'
import { WORKSPACE_SHEET } from './export'
import { readWorkbook, type ReadWorkbook, type WorkbookCellValue } from './reader'

/** Warum ein Wert der Mappe nicht unverändert übernommen wurde. */
export type ImportReason =
  /** Auswahlwert in anderer Schreibweise; dem Listeneintrag zugeordnet. */
  | 'normalized'
  /** Zahl stand als Text in der Zelle; als Zahl gelesen. */
  | 'number-from-text'
  /** Zelle trägt eine eigene Formel; ihr berechneter Wert wurde übernommen. */
  | 'formula-value'
  /** Zahl in einem Textfeld (z. B. ein Datum); als Text übernommen. */
  | 'number-as-text'
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
      /** Zuletzt berechnete Werte der Formelzellen der Mappe, für den Vergleich mit der Webfassung. */
      cached: Record<SheetId, CellMap>
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
  if (field.type === 'text') return typeof raw === 'number' ? { value: String(raw), reason: 'number-as-text' } : { value: raw }
  return readNumber(raw)
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

  sheet(sheet: AvailableSheet): { inputs: CellMap; filled: boolean; cached: CellMap } {
    const cells = this.workbook.cells(sheet.id)
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
}

/** Zuletzt berechnete Werte der Formel- und Ergebniszellen eines Blatts der Mappe. */
function cachedResults(sheet: AvailableSheet, cells: ReadonlyMap<string, WorkbookCellValue>): CellMap {
  const cached: Record<string, CellValue> = {}
  const computed = fieldsOf(sheet.definition).filter((field) => !field.web && (field.kind === 'formula' || field.kind === 'result'))
  for (const address of computed.flatMap((field) => [...cellsOf(field), ...(field.total ? [field.total] : [])])) {
    const value = cells.get(address)?.value
    cached[address] = typeof value === 'boolean' || value === undefined || value === '' ? null : value
  }
  return cached
}

/**
 * Liest eine `.xlsx`-Datei. Blätter der Vorlage ohne Rechenkern werden unter
 * `pending` genannt und noch nicht gelesen.
 */
export function importWorkbook(data: Uint8Array | ArrayBuffer, sheets: readonly SheetModule[] = SHEETS): WorkbookImport {
  const workbook = readWorkbook(data instanceof Uint8Array ? data : new Uint8Array(data))
  if (workbook.sheetNames.includes(WORKSPACE_SHEET)) return { kind: 'workspace', text: workspaceText(workbook) }
  const present = sheets.filter((sheet) => workbook.sheetNames.includes(sheet.id))
  if (present.length === 0) return { kind: 'unknown' }
  const reader = new TemplateReader(workbook, createContext().parameters)
  const inputs: Record<SheetId, CellMap | readonly CellMap[]> = {}
  const cached: Record<SheetId, CellMap> = {}
  const filled: SheetId[] = []
  for (const sheet of present) {
    if (!sheet.available) continue
    const read = reader.sheet(sheet)
    // Ein Listenblatt der Vorlage ist eine Einheit; Vorgaben der Webfelder kommen dazu.
    const isList = sheet.definition.layout === 'list'
    inputs[sheet.id] = isList ? (read.filled ? [{ ...defaultInputs(sheet.definition), ...read.inputs }] : []) : read.inputs
    cached[sheet.id] = read.cached
    if (read.filled) filled.push(sheet.id)
  }
  return { kind: 'template', sheets: inputs, filled, pending: present.filter((sheet) => !sheet.available).map((sheet) => sheet.id), issues: reader.issues, cached }
}
