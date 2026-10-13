/**
 * Anzeigemodell des Berichts (Blatt 20, Druckfassung für die Kommission): die
 * Druckseite als Daten – Kopf, Abschnitte mit Freitexten, Tabellen und
 * Kennzahlen, Fußzeile – und die Hinweise, die auf dem Ausdruck stehen müssen.
 * Rein und ohne Framework; die Oberfläche stellt nur dar. Die Texte der Seite
 * stammen wörtlich aus der Vorlage (`sheets/20_Druck_KOM`).
 */
import { formatPercent } from '@auditcore/common'
import { isBlank, isNumber } from '../excel/index'
import { formatFieldValue } from '../format/numbers'
import type { Translate } from '../i18n/messages'
import { findField, type FieldDefinition } from '../model/definition'
import { evaluateSheet } from '../model/evaluate'
import { createContext, type AvailableSheet, type SheetModule } from '../model/sheet'
import { translateValue } from '../model/texts'
import type { CellAddress, CellMap, CellValue, SheetContext, Tone } from '../model/types'
import { PLACEHOLDERS } from '../sheets/20_Druck_KOM/definition'
import { REPORT_LAYOUT, type ReportBlockLayout, type ReportRowLayout } from '../sheets/20_Druck_KOM/layout'
import { SHEETS, findAvailableSheet } from '../sheets/registry'
import { buildSections, inputName, type RowView } from './sheetView'

/** Zelle einer Tabelle des Berichts. */
export interface ReportCell {
  cell: CellAddress | null
  /** Formatierter Wert, wie er gedruckt wird; leer, wenn die Zelle keinen Wert hat. */
  text: string
  /** Zahl (rechtsbündig, Ziffern gleicher Breite). */
  numeric: boolean
  /** Anzahl der Spalten, über die die Zelle reicht. */
  span: number
  /** Eingabefeld der Zelle (Tabelle der Fehlerfälle), sonst `null`. */
  input: RowView | null
  /** „Angabe fehlt“: Die Vorlage rechnete hier mit 0 weiter. */
  missing: boolean
}

export interface ReportRow {
  key: string
  /** Zeilenbeschriftung (Spalte A der Vorlage) oder leer. */
  header: string
  cells: readonly ReportCell[]
}

export type ReportBlock =
  | { kind: 'text'; key: string; field: RowView; placeholder: string; text: string }
  | { kind: 'table'; key: string; columns: readonly { label: string; numeric: boolean }[]; rows: readonly ReportRow[]; foot: ReportRow | null }
  | { kind: 'statement'; key: string; text: string }

export interface ReportSection {
  id: string
  title: string
  blocks: readonly ReportBlock[]
}

/** Hinweis zum Bericht; `printed`: steht auf dem Ausdruck. */
export interface ReportHint {
  id: string
  text: string
  tone: Tone
  printed: boolean
}

/** Die Berichtsseite als Daten. */
export interface ReportPage {
  title: string
  /** Zeilen neben dem Emblem („Kofinanziert von der“ / „Europäischen Union“). */
  cofinanced: readonly string[]
  /** Programm, CCI, Geschäftsjahr und Status. */
  subtitle: string
  /** „Stand …“ oder leer. */
  asOf: string
  sections: readonly ReportSection[]
  /** Steuerfelder; sie werden nicht gedruckt. */
  controls: { title: string; note: string; fields: readonly RowView[] }
  hints: readonly ReportHint[]
  /** Einordnung und Stand der Vorlage; stehen auf dem Ausdruck. */
  notes: readonly string[]
  footer: string
  labels: { report: string; print: string; hints: string }
}

/** Texte der Berichtsansicht, die `i18n/messages.ts` noch nicht führt, mit deutschem Wortlaut als Rückfall. */
const REPORT_TEXTS = { reportPrint: 'Drucken / als PDF sichern' } as const

function reportText(t: Translate, key: keyof typeof REPORT_TEXTS): string {
  try {
    const text = (t as (key: string) => string | undefined)(key)
    return text && text !== key ? text : REPORT_TEXTS[key]
  } catch {
    return REPORT_TEXTS[key]
  }
}

/** Tag 0 der Tabellenkalkulation (30.12.1899) für Datumswerte, die als Zahl vorliegen. */
const SERIAL_EPOCH = Date.UTC(1899, 11, 30)
const DAY = 86400000

/** Datum wie im Format `dd.mm.yyyy` der Vorlage; Texte bleiben, wie sie eingegeben sind. */
function dateText(value: CellValue): string {
  if (!isNumber(value)) return isBlank(value) ? '' : String(value)
  const date = new Date(SERIAL_EPOCH + Math.round(value) * DAY)
  const two = (part: number): string => String(part).padStart(2, '0')
  return `${two(date.getUTCDate())}.${two(date.getUTCMonth() + 1)}.${date.getUTCFullYear()}`
}

const isNumeric = (field: FieldDefinition | undefined): boolean => field !== undefined && ['amount', 'integer', 'percent', 'decimal'].includes(field.type)

/** Zahl im Zahlenformat der Vorlage: Nachkommastellen der Prozentwerte und der Text für 0 (`…;"nicht erforderlich"`). */
function formatNumber(sheet: AvailableSheet, field: FieldDefinition, value: number): string {
  const format = field.format ?? ''
  const zero = /;"([^"]*)"$/.exec(format)?.[1]
  if (zero && value === 0) return translateValue(sheet.texts, zero)
  if (field.type === 'percent') return formatPercent(value, { digits: /0\.(0+)%/.exec(format)?.[1]?.length ?? 2 })
  return formatFieldValue(field, value)
}

/** Wert, wie er gedruckt wird; Texte der Vorlage in der Sprache des Blatts. */
function formatValue(sheet: AvailableSheet, field: FieldDefinition | undefined, value: CellValue): string {
  if (isBlank(value)) return ''
  return isNumber(value) && field ? formatNumber(sheet, field, value) : translateValue(sheet.texts, String(value))
}

interface Scope {
  sheet: AvailableSheet
  results: CellMap
  rows: ReadonlyMap<CellAddress, RowView>
  lacking: ReadonlyMap<CellAddress, readonly string[]>
  t: Translate
}

const translated = (scope: Scope, text: string): string => translateValue(scope.sheet.texts, text)

function cellOf(scope: Scope, entry: ReportRowLayout['cells'][number]): ReportCell {
  if (!entry) return { cell: null, text: '', numeric: false, span: 1, input: null, missing: false }
  const field = findField(scope.sheet.definition, entry.cell)
  const row = scope.rows.get(entry.cell)
  const value = scope.results[entry.cell] ?? null
  const missing = isBlank(value) && (scope.lacking.get(entry.cell)?.length ?? 0) > 0
  return {
    cell: entry.cell,
    text: missing ? scope.t('missing') : formatValue(scope.sheet, field, value),
    numeric: isNumeric(field),
    span: entry.span ?? 1,
    input: row && row.kind === 'input' ? row : null,
    missing,
  }
}

function rowOf(scope: Scope, layout: ReportRowLayout, key: string): ReportRow {
  return { key, header: layout.label ? translated(scope, layout.label) : '', cells: layout.cells.map((entry) => cellOf(scope, entry)) }
}

/** Freitext: Der Platzhalter ist die Bezeichnung des Felds (bei einer Übersetzung des Blatts in dessen Sprache). */
function textOf(scope: Scope, cell: CellAddress, key: string): ReportBlock | null {
  const field = scope.rows.get(cell)
  const value = scope.results[cell] ?? null
  return field ? { kind: 'text', key, field, placeholder: field.label || PLACEHOLDERS[cell as keyof typeof PLACEHOLDERS], text: isBlank(value) ? '' : String(value) } : null
}

function blockOf(scope: Scope, layout: ReportBlockLayout, key: string): ReportBlock | null {
  if (layout.kind === 'statement') return { kind: 'statement', key, text: formatValue(scope.sheet, undefined, scope.results[layout.cell] ?? null) }
  if (layout.kind === 'text') return textOf(scope, layout.cell, key)
  const rows = layout.rows.map((row, index) => rowOf(scope, row, `${key}-${index}`))
  // Spalten mit Zahlen: nach der ersten Zeile; die Beschriftungsspalte zählt nicht mit.
  const offset = layout.rows[0]?.label ? 1 : 0
  const columns = layout.columns.map((label, index) => ({ label: translated(scope, label), numeric: rows[0]?.cells[index - offset]?.numeric ?? false }))
  return { kind: 'table', key, columns, rows, foot: layout.foot ? rowOf(scope, layout.foot, `${key}-foot`) : null }
}

/** Blatt, dessen Hinweise auf den Ausdruck gehören, mit dem Kontext, in dem es gerechnet ist. */
interface Source {
  sheet: AvailableSheet
  context: SheetContext
  /** Hinweise der Webfassung des Blatts mitdrucken (Blatt 18); beim Verfahren nur die mit 0 gerechneten Eingaben. */
  webHints: boolean
}

/** Das in Blatt 18 übernommene Verfahren und Blatt 18 selbst. */
function sources(context: SheetContext, sheets: readonly SheetModule[]): Source[] {
  const base = createContext({ parameters: context.parameters, sheets: context.sheets, policy: context.policy })
  const total = findAvailableSheet('18_GFQ_AnhIII', sheets)
  const adopted = total ? context.sheets[total.id]?.C4 : null
  const method = typeof adopted === 'string' ? findAvailableSheet(adopted, sheets) : undefined
  return [...(method ? [{ sheet: method, context: base, webHints: false }] : []), ...(total ? [{ sheet: total, context: { ...base, method: context.method }, webHints: true }] : [])]
}

/** Hinweise eines liefernden Blatts: jede mit 0 gerechnete Eingabe und – bei Blatt 18 – die Hinweise der Webfassung. */
function sourceHints(source: Source, cells: CellMap, t: Translate): ReportHint[] {
  const prefix = t('sheetNumber', { number: source.sheet.definition.number })
  const zero = evaluateSheet(source.sheet, cells, source.context).assumed.map((entry): ReportHint => ({
    id: `${source.sheet.id}-zero-${entry.input}`,
    tone: 'warning',
    printed: true,
    text: `${prefix}: ${t('zeroAssumedInput', { input: inputName(source.sheet, entry.input) })}`,
  }))
  const web = source.webHints ? (source.sheet.webHints?.(cells, cells, source.context) ?? []) : []
  return [...zero, ...web.map((hint): ReportHint => ({ id: `${source.sheet.id}-${hint.id}`, tone: hint.tone, printed: true, text: `${prefix}: ${hint.text}` }))]
}

/**
 * Hinweise zum Bericht: gedruckt werden die Hinweise des Verfahrens und des
 * Blatts 18, nur am Bildschirm stehen die Hinweise der Webfassung zu Blatt 20.
 * Die liefernden Blätter rechnen dafür auf ihren Zellwerten aus dem Kontext;
 * diese enthalten die Eingaben.
 */
function hintsOf(sheet: AvailableSheet, inputs: CellMap, results: CellMap, context: SheetContext, t: Translate, sheets: readonly SheetModule[]): ReportHint[] {
  const printed = sources(context, sheets).flatMap((source) => sourceHints(source, context.sheets[source.sheet.id] ?? {}, t))
  const own = (sheet.webHints?.(inputs, results, context) ?? []).map((hint): ReportHint => ({ ...hint, text: sheet.texts?.webHints?.[hint.id] ?? hint.text, printed: false }))
  return [...printed, ...own]
}

/**
 * Berichtsseite aus dem Blatt 20, seinen Eingaben und Ergebnissen. `context` ist
 * der Kontext des Arbeitsstands (`contextFor('20_Druck_KOM', …)`) mit den
 * Ergebnissen aller Blätter und der Ergebnisübersicht des aktiven Verfahrens;
 * `sheets` der Blattbestand der Anwendung.
 */
export function buildReport(sheet: AvailableSheet, inputs: CellMap, results: CellMap, context: SheetContext, t: Translate, sheets: readonly SheetModule[] = SHEETS): ReportPage {
  const rows = new Map(buildSections(sheet, inputs, results, context, t).flatMap((section) => section.rows.map((row) => [row.cell, row] as const)))
  const scope: Scope = { sheet, results, rows, lacking: evaluateSheet(sheet, inputs, context).lacking, t }
  const asOf = results[REPORT_LAYOUT.asOf] ?? null
  const prefix = /^"([^"]*)"/.exec(findField(sheet.definition, REPORT_LAYOUT.asOf)?.format ?? '')?.[1] ?? ''
  return {
    title: sheet.definition.title,
    cofinanced: REPORT_LAYOUT.cofinanced.map((line) => translated(scope, line)),
    subtitle: formatValue(sheet, undefined, results[REPORT_LAYOUT.subtitle] ?? null),
    asOf: isBlank(asOf) ? '' : `${translated(scope, prefix)}${dateText(asOf)}`,
    sections: REPORT_LAYOUT.sections.map((section) => ({
      id: section.id,
      title: translated(scope, section.title),
      blocks: section.blocks.flatMap((block, index) => blockOf(scope, block, `${section.id}-${index}`) ?? []),
    })),
    controls: {
      title: translated(scope, REPORT_LAYOUT.controls.title),
      note: translated(scope, REPORT_LAYOUT.controls.note),
      fields: REPORT_LAYOUT.controls.cells.flatMap((cell) => rows.get(cell) ?? []),
    },
    hints: hintsOf(sheet, inputs, results, context, t, sheets),
    notes: [t('disclaimer'), t('templateStatus')],
    footer: translated(scope, REPORT_LAYOUT.footer),
    labels: { report: t('stepReport'), print: reportText(t, 'reportPrint'), hints: t('webHint') },
  }
}
