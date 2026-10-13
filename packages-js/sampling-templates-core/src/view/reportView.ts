/**
 * Anzeigemodell des Berichts (Blatt 20, Druckfassung für die Kommission): die
 * Druckseite als Daten – Kopf, Abschnitte mit Freitexten, Tabellen und
 * Kennzahlen, Fußzeile – und die Hinweise, die auf dem Ausdruck stehen müssen.
 * Rein und ohne Framework; die Oberfläche stellt nur dar. Die Texte der Seite
 * stammen wörtlich aus der Vorlage (`sheets/20_Druck_KOM`); nur Programm und
 * Prüfbehörde in Kopf- und Fußzeile sind Angaben der Prüfbehörde.
 */
import { formatPercent } from '@auditcore/common'
import { isBlank, isNumber, left } from '../excel/index'
import { formatFieldValue } from '../format/numbers'
import type { Translate } from '../i18n/messages'
import { findField, type FieldDefinition } from '../model/definition'
import { evaluateSheet } from '../model/evaluate'
import type { AvailableSheet, SheetModule } from '../model/sheet'
import { translateValue } from '../model/texts'
import type { CellAddress, CellMap, CellValue, SheetContext, Tone } from '../model/types'
import { PLACEHOLDERS } from '../sheets/20_Druck_KOM/definition'
import { REPORT_LAYOUT, type ReportBlockLayout, type ReportRowLayout } from '../sheets/20_Druck_KOM/layout'
import { SHEETS } from '../sheets/registry'
import { ENGINE_VERSION, LEGAL_STATE, TEMPLATE_NAME } from '../workspace/types'
import { carriedLimitations } from './limits'
import { buildSections, type RowView } from './sheetView'

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
  /** Programm, CCI, Geschäftsjahr und Status in der Sprache des Blatts. */
  subtitle: string
  /** Platzhalter für die Bezeichnung des Programms, solange sie fehlt; nur am Bildschirm, nie im Druck. */
  programmePlaceholder: string
  /** „Stand …“ oder leer. */
  asOf: string
  sections: readonly ReportSection[]
  /** Steuerfelder; sie werden nicht gedruckt. */
  controls: { title: string; note: string; fields: readonly RowView[] }
  hints: readonly ReportHint[]
  /** Einordnung und Stand der Vorlage; stehen auf dem Ausdruck. */
  notes: readonly string[]
  /**
   * Zuordnung des Ausdrucks zu einem Arbeitsstand, wie im Kopf des Excel-Exports:
   * Vorlage, Rechtsstand und Fassung des Rechenkerns. Die Prüfsumme der Eingaben
   * ergänzt die Oberfläche (sie wird asynchron gebildet).
   */
  identity: readonly { label: string; value: string }[]
  /** Beschriftung der Prüfsumme der Eingaben. */
  checksumLabel: string
  /** Prüfbehörde, Organisationseinheit und Ort nach den Angaben der Prüfbehörde; leer, solange sie fehlen. */
  footer: string
  /** Platzhalter für die Fußzeile, solange die Prüfbehörde fehlt; nur am Bildschirm, nie im Druck. */
  footerPlaceholder: string
  labels: { report: string; print: string; hints: string }
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

/**
 * Hinweise zum Bericht. Gedruckt wird alles, was die Aussagekraft des
 * Ergebnisses einschränkt: die Einschränkungen des gewählten Verfahrens und des
 * Blatts 18 (mit 0 gerechnete Eingaben, Werte ohne Grundlage, Hinweise in
 * Warnfarbe, Auslegungen der Vorlage, Altvorlage) und die eigenen Warnhinweise
 * des Berichts. Nur am Bildschirm stehen die übrigen Hinweise zu Blatt 20.
 */
function hintsOf(sheet: AvailableSheet, inputs: CellMap, results: CellMap, context: SheetContext, t: Translate, sheets: readonly SheetModule[]): ReportHint[] {
  const carried = carriedLimitations(sheet, context, t, sheets).map((entry): ReportHint => ({ id: entry.id, tone: entry.tone, printed: true, text: entry.text }))
  const own = (sheet.webHints?.(inputs, results, context) ?? []).map((hint): ReportHint => ({ ...hint, text: sheet.texts?.webHints?.[hint.id] ?? hint.text, printed: hint.tone === 'warning' || hint.tone === 'danger' }))
  return [...carried, ...own]
}

/** Platzhalter am Bildschirm, solange die Angabe fehlt. */
const placeholder = (value: CellValue | undefined, text: string): string => (isBlank(value) ? text : '')

const PROGRAMME = 'W4'
const POPULATION_SHEET = '02_Grundgesamtheit'
/** Zeichen der CCI-Nummer, die die Vorlage in die Kopfzeile übernimmt (`LEFT(…;15)`). */
const CCI_LENGTH = 15

/**
 * Kopfzeile: Programm · CCI · Geschäftsjahr · Status. Dieselben Teile wie in
 * Zelle A6, hier in der Sprache des Blatts; das Programm ist die Angabe der
 * Prüfbehörde, kein fester Text.
 */
function subtitleOf(scope: Scope, context: SheetContext): string {
  const population = context.sheets[POPULATION_SHEET] ?? {}
  const word = (value: CellValue | undefined): string => (isBlank(value) ? '' : translated(scope, String(value)))
  const parts = [word(scope.results[PROGRAMME]), `CCI ${left(population.C9, CCI_LENGTH)}`, `${translated(scope, 'Geschäftsjahr')} ${word(population.C12)}`, word(scope.results.J5)]
  return parts.filter(Boolean).join(' · ')
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
    subtitle: subtitleOf(scope, context),
    programmePlaceholder: placeholder(results[PROGRAMME], t('reportProgrammeMissing')),
    asOf: isBlank(asOf) ? '' : `${translated(scope, prefix)}${dateText(asOf)}`,
    sections: REPORT_LAYOUT.sections.map((section) => ({
      id: section.id,
      title: translated(scope, section.title),
      blocks: section.blocks.flatMap((block, index) => blockOf(scope, block, `${section.id}-${index}`) ?? []),
    })),
    controls: {
      title: translated(scope, REPORT_LAYOUT.controls.title),
      note: translated(scope, REPORT_LAYOUT.controls.note),
      fields: [...REPORT_LAYOUT.identity, ...REPORT_LAYOUT.controls.cells].flatMap((cell) => rows.get(cell) ?? []),
    },
    hints: hintsOf(sheet, inputs, results, context, t, sheets),
    notes: [t('disclaimer'), t('templateStatus')],
    identity: [
      { label: t('exportTemplate'), value: TEMPLATE_NAME },
      { label: t('exportLegalState'), value: LEGAL_STATE },
      { label: t('exportEngine'), value: ENGINE_VERSION },
    ],
    checksumLabel: t('exportChecksum'),
    footer: formatValue(sheet, undefined, results[REPORT_LAYOUT.footer] ?? null),
    footerPlaceholder: placeholder(results[REPORT_LAYOUT.footer], t('reportAuthorityMissing')),
    labels: { report: t('stepReport'), print: t('reportPrint'), hints: t('webHint') },
  }
}
