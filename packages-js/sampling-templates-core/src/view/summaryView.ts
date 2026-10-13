/**
 * Anzeigemodell der mitlaufenden Ergebnisspalte: Hauptgröße, Kennzahlen,
 * Skala gegen die Wesentlichkeitsschwelle und alle Prüfhinweise.
 */
import { formatPercent } from '@auditcore/common'
import { isBlank, isNumber, toneOf } from '../excel/index'
import { formatFieldValue } from '../format/numbers'
import type { Translate } from '../i18n/messages'
import { cellsOf, fieldsOf, findField, inputFields, type FieldDefinition, type SummaryDefinition } from '../model/definition'
import { evaluateSheet } from '../model/evaluate'
import type { AvailableSheet } from '../model/sheet'
import { translateValue } from '../model/texts'
import type { CellMap, CellValue, SheetContext, Tone } from '../model/types'
import { inputName } from './sheetView'

export interface HintView {
  id: string
  text: string
  tone: Tone
  /** `template`: Prüfhinweis der Vorlage, wortgleich; `web`: Hinweis der Webfassung. */
  source: 'template' | 'web'
}

export interface GaugeView {
  /** Positionen von 0 bis 1 auf der Skala. */
  threshold: number
  rate: number
  upper: number | null
  thresholdLabel: string
  maxLabel: string
  /** Bezeichnung der Quote in der Legende. */
  rateLabel: string
  /** Bezeichnung der oberen Grenze; `null`, wenn das Blatt keine hat. */
  upperLabel: string | null
  /** Beschreibung für Screenreader. */
  description: string
}

export interface SummaryView {
  primaryLabel: string
  /** Formatierte Hauptgröße oder leer, wenn sie fehlt. */
  primaryValue: string
  primaryUnit: string
  /** Erklärung, wenn die Hauptgröße nicht bestimmbar ist. */
  primaryNote: string
  rows: readonly { label: string; value: string; strong: boolean }[]
  gauge: GaugeView | null
  hints: readonly HintView[]
}

const GAUGE_MIN = 0.03

const percent = (value: number): string => formatPercent(value, { digits: 2 })

/** Bezeichnungen der Skala: Begriffe des Blatts, sonst die der Oberfläche; ohne obere Fehlergrenze im Blatt keine. */
function gaugeLabels(gauge: NonNullable<SummaryDefinition['gauge']>, t: Translate): { rateLabel: string; upperLabel: string | null } {
  return { rateLabel: gauge.rateLabel ?? t('gaugeRate'), upperLabel: gauge.upper ? (gauge.upperLabel ?? t('gaugeUpper')) : null }
}

function gaugeOf(sheet: AvailableSheet, results: CellMap, t: Translate): GaugeView | null {
  const gauge = sheet.definition.summary.gauge
  if (!gauge) return null
  const threshold = results[gauge.threshold]
  const rate = results[gauge.rate]
  const upper = gauge.upper ? results[gauge.upper] : null
  if (!isNumber(threshold) || !isNumber(rate)) return null
  const top = isNumber(upper) ? upper : rate
  const max = Math.max(threshold * 2, top * 1.15, GAUGE_MIN)
  const position = (value: number): number => Math.min(1, Math.max(0, value) / max)
  const labels = gaugeLabels(gauge, t)
  const upperText = labels.upperLabel ? [`${labels.upperLabel} ${isNumber(upper) ? percent(upper) : '–'}`] : []
  return {
    threshold: position(threshold),
    rate: position(rate),
    upper: isNumber(upper) ? position(upper) : null,
    thresholdLabel: t('gaugeThreshold', { threshold: percent(threshold) }),
    maxLabel: percent(max),
    ...labels,
    description: [`${labels.rateLabel} ${percent(rate)}`, ...upperText, t('gaugeThresholdLong', { threshold: percent(threshold) })].join(', '),
  }
}

/** Prüfhinweise einer Schichtzeile: je Schicht mit Befund eine Zeile, sonst eine gemeinsame. */
function strataHints(sheet: AvailableSheet, field: FieldDefinition, results: CellMap, t: Translate): HintView[] {
  const found = cellsOf(field)
    .map((cell, index) => ({ cell, index, value: results[cell] }))
    .filter((entry) => !isBlank(entry.value))
  const text = (value: unknown): string => translateValue(sheet.texts, String(value))
  const problems = found.filter((entry) => toneOf(entry.value) !== 'success')
  if (found.length > 0 && problems.length === 0) return [{ id: field.cell, text: `${field.label}: ${text(found[0]!.value)}`, tone: 'success', source: 'template' }]
  return problems.map((entry) => ({ id: entry.cell, text: `${t('stratum', { number: entry.index + 1 })}: ${text(entry.value)}`, tone: toneOf(entry.value), source: 'template' }))
}

/** Prüfhinweise der Vorlage in Blattreihenfolge, danach die Hinweise der Webfassung. */
export function buildHints(sheet: AvailableSheet, inputs: CellMap, results: CellMap, context: SheetContext, t: Translate): HintView[] {
  const template = fieldsOf(sheet.definition)
    .filter((field) => field.type === 'check')
    .flatMap((field): HintView[] => {
      if (field.columns) return strataHints(sheet, field, results, t)
      const value = results[field.cell]
      return isBlank(value) ? [] : [{ id: field.cell, text: translateValue(sheet.texts, String(value)), tone: toneOf(value), source: 'template' }]
    })
  const web = (sheet.webHints?.(inputs, results, context) ?? []).map((hint): HintView => ({ ...hint, text: sheet.texts?.webHints?.[hint.id] ?? hint.text, source: 'web' }))
  // Als 0 gerechnete fehlende Eingaben: in Warnfarbe neben den Prüfhinweisen der Vorlage.
  const assumed = evaluateSheet(sheet, inputs, context).assumed.map((entry): HintView => ({ id: `zero-${entry.input}`, tone: 'warning', source: 'web', text: t('zeroAssumedInput', { input: inputName(sheet, entry.input) }) }))
  return [...template, ...assumed, ...web]
}

/** Warum die Hauptgröße fehlt: Text der Vorlage („TE ≤ AE“) oder die fehlenden Eingaben. */
function primaryNote(sheet: AvailableSheet, inputs: CellMap, context: SheetContext, reason: CellValue, t: Translate): string {
  if (typeof reason === 'string' && reason) return `${t('notDeterminable')} (${translateValue(sheet.texts, reason)})`
  const lacking = evaluateSheet(sheet, inputs, context).lacking.get(sheet.definition.summary.primary.cell) ?? []
  return lacking.length ? `${t('missing')}. ${t('missingInputs', { inputs: [...new Set(lacking)].map((input) => inputName(sheet, input)).join('; ') })}` : ''
}

/**
 * Leeres Formular: Keine Eingabe weicht von den Vorgaben der Vorlage ab und keine
 * Verknüpfung liefert einen Wert. Die Ergebnisspalte zeigt dann „noch keine
 * Angaben“ und keine Prüfhinweise – ein bestandener Hinweis zu einer bloßen
 * Vorgabe sähe wie ein Ergebnis aus.
 */
export function isEmptyForm(sheet: AvailableSheet, results: CellMap, context?: SheetContext): boolean {
  // Blatt 18 übernimmt Werte des gewählten Verfahrens: Mit ihnen ist es nicht leer, auch ohne eigene Eingabe.
  if (context?.method && Object.values(context.method).some((value) => isNumber(value))) return false
  return inputFields(sheet.definition).every((field) => cellsOf(field).every((cell) => isBlank(results[cell]) || results[cell] === (field.default ?? null)))
}

/** Mitlaufende Ergebnisspalte eines Blatts. */
export function buildSummary(sheet: AvailableSheet, inputs: CellMap, results: CellMap, context: SheetContext, t: Translate): SummaryView {
  const { primary, rows } = sheet.definition.summary
  const value = results[primary.cell] ?? null
  const field = findField(sheet.definition, primary.cell)
  const reason = primary.reason ? results[primary.reason] : null
  const empty = isEmptyForm(sheet, results, context)
  const note = (): string => (empty ? t('noEntries') : primaryNote(sheet, inputs, context, reason ?? null, t))
  return {
    primaryLabel: primary.label,
    primaryValue: isNumber(value) && field ? formatFieldValue(field, value) : '',
    primaryUnit: isNumber(value) ? primary.unit : '',
    primaryNote: isNumber(value) ? '' : note(),
    rows: rows.map((row) => {
      const rowField = findField(sheet.definition, row.cell)
      return { label: row.label, value: rowField ? formatFieldValue(rowField, results[row.cell]) : '', strong: row.strong ?? false }
    }),
    gauge: gaugeOf(sheet, results, t),
    hints: empty ? [] : buildHints(sheet, inputs, results, context, t),
  }
}
