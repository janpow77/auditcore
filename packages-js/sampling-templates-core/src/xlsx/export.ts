/**
 * Ergebnisexport als `.xlsx`: Blatt „Ergebnis“ mit Kopfblock und je Zeile
 * Abschnitt, Bezeichnung, Wert, Art, Fundstelle und Zelle der Vorlage; weitere
 * bearbeitete Blätter folgen. Das ausgeblendete Blatt `_Arbeitsstand` trägt
 * den Arbeitsstand, sodass sich die Datei wieder öffnen lässt.
 */
import { formatDateTime } from '@auditcore/common'
import { isBlank } from '../excel/index'
import { formatFieldValue } from '../format/numbers'
import { createTranslate, type MessageKey, type Translate } from '../i18n/messages'
import { cellsOf, fieldsOf, type FieldDefinition, strataColumnsOf } from '../model/definition'
import { createContext, type AvailableSheet, type SheetModule } from '../model/sheet'
import type { CellMap, CellValue, SheetContext } from '../model/types'
import { SHEETS } from '../sheets/registry'
import { TEMPLATE_STRATA, usedStrata } from '../model/strata'
import { strataRows } from '../view/sheetView'
import { buildHints } from '../view/summaryView'
import { contextFor, computeWorkspace, listRows } from '../workspace/compute'
import { exportFileName } from '../workspace/filenames'
import { saveWorkspace } from '../workspace/save'
import { LEGAL_STATE, TEMPLATE_NAME, type WorkspaceFile, type WorkspaceState } from '../workspace/types'
import { XLSX_MEDIA_TYPE, writeWorkbook, type CellStyle, type WorkbookCell, type WorkbookSheet } from './writer'

/** Name des ausgeblendeten Blatts mit dem Arbeitsstand. */
export const WORKSPACE_SHEET = '_Arbeitsstand'
/** Zeichen je Zelle; Excel fasst höchstens 32.767 Zeichen. */
const CHUNK = 30000
const WIDTHS = [30, 62, 22, 16, 60, 16]
/** Farben nach der Legende der Vorlage: Eingabe gelb/blau, Verknüpfung gelb/grün, Ergebnis grün und fett. */
const INPUT: CellStyle = { fill: 'FFF2CC', color: '1F4E9D' }
const LINK: CellStyle = { fill: 'FFF2CC', color: '2E7D32' }
const RESULT: CellStyle = { fill: 'E2EFDA', bold: true }
const HEAD: CellStyle = { bold: true, fill: 'E7E6E6', wrap: true }
const WRAP: CellStyle = { wrap: true }

export interface ExportOptions {
  sheets?: readonly SheetModule[]
  now?: Date
  /** Texte des Exports (Standard: deutsch). */
  t?: Translate
  /** Vorsatz des Dateinamens (Standard: „Stichprobe“). */
  filePrefix?: string
}

/** Fertige Exportdatei. */
export interface ExportedWorkbook {
  data: Uint8Array
  fileName: string
  mediaType: string
}

const KIND_KEYS: Readonly<Record<FieldDefinition['kind'], MessageKey>> = { input: 'kindInput', link: 'kindLink', formula: 'kindFormula', result: 'kindResult' }

const text = (value: string, style: CellStyle = WRAP): WorkbookCell => ({ value, style })

function valueCell(field: FieldDefinition, value: CellValue): WorkbookCell | null {
  if (isBlank(value)) return null
  const base = field.kind === 'result' ? RESULT : field.kind === 'input' ? INPUT : field.kind === 'link' ? LINK : {}
  if (typeof value === 'number') return { value, style: { ...base, format: field.format } }
  return { value: formatFieldValue(field, value), style: { ...base, wrap: true } }
}

function headerRows(sheet: AvailableSheet, file: WorkspaceFile, t: Translate): (WorkbookCell | null)[][] {
  const { definition } = sheet
  const pairs: [MessageKey, string][] = [
    ['exportMethod', definition.title],
    ['exportSheetName', definition.sheet],
    ['exportLegalBasis', definition.legalBasis],
    ['exportTemplate', TEMPLATE_NAME],
    ['exportLegalState', LEGAL_STATE],
    ['exportDate', formatDateTime(file.gespeichertAm)],
    ['exportEngine', file.rechenkern],
    ['exportChecksum', file.pruefsumme],
  ]
  return [[text(t('title'), { bold: true })], ...pairs.map(([key, value]) => [text(t(key), { bold: true }), text(value)]), [text(t('disclaimer'))], [text(t('templateStatus'))], []]
}

/** Zellbezug einer Zeile: einzelne Zelle oder der Bereich der belegten Schichtspalten. */
function reference(field: FieldDefinition, strata: number): string {
  if (!field.columns) return field.cell
  const cells = cellsOf(field).slice(0, strata)
  const range = cells.length > 1 ? `${cells[0]}:${cells.at(-1)}` : (cells[0] ?? field.cell)
  return field.total ? `${field.total}; ${range}` : range
}

/** Fundstelle bzw. Hinweis der Vorlage; eine Auslegung der Vorlage ist als solche gekennzeichnet. */
function referenceText(field: FieldDefinition, t: Translate): string {
  return [field.hint, field.interpretation ? `${t('interpretation')}: ${field.interpretation}` : ''].filter(Boolean).join(' ')
}

function fieldRows(sheet: AvailableSheet, results: CellMap, strata: number, t: Translate): (WorkbookCell | null)[][] {
  return sheet.definition.sections.flatMap((section) =>
    section.fields.map((field) => [
      text(`${section.id} · ${section.title}`),
      text(field.formula ? `${field.label} (${field.formula})` : field.label),
      valueCell(field, results[field.columns ? (field.total ?? '') : field.cell] ?? null),
      text(t(field.web ? 'kindWebHint' : field.type === 'check' ? 'kindCheck' : KIND_KEYS[field.kind])),
      text(referenceText(field, t)),
      text(reference(field, strata)),
      ...(field.columns ? cellsOf(field).slice(0, strata).map((cell) => valueCell(field, results[cell] ?? null)) : []),
    ]),
  )
}

/** Anzahl der Schichtspalten im Export: die belegten Schichten des Blatts. */
function strataCount(sheet: AvailableSheet, inputs: CellMap): number {
  const rows = strataRows(sheet)
  return rows.length ? Math.max(1, usedStrata(inputs, rows, strataColumnsOf(sheet.definition))) : 0
}

function resultSheet(name: string, sheet: AvailableSheet, inputs: CellMap, results: CellMap, context: SheetContext, file: WorkspaceFile, t: Translate): WorkbookSheet {
  const columns: MessageKey[] = ['columnSection', 'columnLabel', 'columnValue', 'columnKind', 'columnReference', 'columnCell']
  const strata = strataCount(sheet, inputs)
  const strataHead = Array.from({ length: strata }, (_, index) => text(t('stratum', { number: index + 1 }), HEAD))
  const beyond = strata > TEMPLATE_STRATA.length ? [[null, text(t('strataBeyondTemplate')), null, text(t('kindWebHint'))]] : []
  const webHints = buildHints(sheet, inputs, results, context, t)
    .filter((hint) => hint.source === 'web')
    .map((hint) => [null, text(hint.text), null, text(t('kindWebHint'))])
  return {
    name,
    widths: [...WIDTHS, ...strataHead.map(() => 18)],
    rows: [...headerRows(sheet, file, t), [...columns.map((key) => text(t(key), HEAD)), ...strataHead], ...fieldRows(sheet, results, strata, t), ...beyond, ...webHints],
  }
}

/** Listenblatt (Blatt 17): je Einheit eine Zeile, je Feld eine Spalte mit Bezeichnung und Zelle. */
function listSheet(sheet: AvailableSheet, rows: readonly CellMap[], file: WorkspaceFile, t: Translate): WorkbookSheet {
  const fields = fieldsOf(sheet.definition)
  const head = fields.map((field) => text(`${field.label} (${field.cell})`, HEAD))
  const body = rows.map((row) => {
    const cells = sheet.compute(row, createContext())
    return fields.map((field) => valueCell(field, cells[field.cell] ?? null))
  })
  return { name: sheet.id, widths: fields.map(() => 24), rows: [...headerRows(sheet, file, t), head, ...body] }
}

/** JSON nur aus ASCII-Zeichen (`\uXXXX`), damit kein Zeichen außerhalb der Grundebene auf einer Stückgrenze zerbricht. */
function asciiJson(value: unknown): string {
  return JSON.stringify(value).replace(/[\u007f-\uffff]/g, (character) => `\\u${character.charCodeAt(0).toString(16).padStart(4, '0')}`)
}

/** Arbeitsstand in Zellen der Spalte A, in Stücken unterhalb der Zeichengrenze von Excel. */
function workspaceSheet(json: string): WorkbookSheet {
  const rows: WorkbookCell[][] = []
  for (let offset = 0; offset < json.length; offset += CHUNK) rows.push([{ value: json.slice(offset, offset + CHUNK) }])
  return { name: WORKSPACE_SHEET, hidden: true, rows }
}

/** Ergebnisblätter: das aktive Verfahren zuerst als „Ergebnis“, danach die weiteren bearbeiteten Blätter. */
function resultSheets(state: WorkspaceState, sheets: readonly SheetModule[], file: WorkspaceFile, t: Translate): WorkbookSheet[] {
  const results = computeWorkspace(state, sheets)
  const pages: WorkbookSheet[] = []
  for (const sheet of sheets) {
    if (!sheet.available) continue
    const page = pageOf(sheet, state, results, file, t)
    if (page && sheet.id === state.activeMethod) pages.unshift(page)
    else if (page) pages.push(page)
  }
  return pages
}

/** Seite eines Blatts oder `null`, wenn es nicht bearbeitet ist. */
function pageOf(sheet: AvailableSheet, state: WorkspaceState, results: Readonly<Record<string, CellMap>>, file: WorkspaceFile, t: Translate): WorkbookSheet | null {
  const active = sheet.id === state.activeMethod
  const computed = results[sheet.id]
  if (sheet.definition.layout === 'list') {
    const rows = listRows(state, sheet.id)
    return rows.length > 0 ? listSheet(sheet, rows, file, t) : null
  }
  const inputs = state.sheets[sheet.id]
  if (!computed || Array.isArray(inputs) || (!active && !inputs)) return null
  return resultSheet(active ? t('exportSheet') : sheet.id, sheet, (inputs as CellMap | undefined) ?? {}, computed, contextFor(sheet.id, state, results), file, t)
}

/** Exportiert das Ergebnis des aktiven Verfahrens und aller weiteren bearbeiteten Blätter. */
export async function exportWorkbook(state: WorkspaceState, options: ExportOptions = {}): Promise<ExportedWorkbook> {
  const sheets = options.sheets ?? SHEETS
  const t = options.t ?? createTranslate()
  const saved = await saveWorkspace(state, { sheets, now: options.now })
  const pages = resultSheets(state, sheets, saved.file, t)
  if (pages.length === 0) pages.push({ name: t('exportSheet'), rows: [[text(t('title'), { bold: true })], [text(t('noValue'))]] })
  const data = writeWorkbook([...pages, workspaceSheet(asciiJson(saved.file))])
  return { data, fileName: exportFileName(state, sheets, options.now, options.filePrefix), mediaType: XLSX_MEDIA_TYPE }
}
