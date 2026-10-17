/**
 * Anzeigemodell der mitlaufenden Ergebnisspalte: Hauptgröße, Kennzahlen,
 * Skala gegen die Signifikanzschwelle und alle Prüfhinweise.
 */
import { formatPercent } from '@auditcore/common'
import { isBlank, isNumber, toneOf } from '../excel/index'
import { formatFieldValue } from '../format/numbers'
import type { Translate } from '../i18n/messages'
import { cellsOf, fieldsOf, findField, inputFields, type FieldDefinition, type SummaryDefinition } from '../model/definition'
import { evaluateSheet } from '../model/evaluate'
import type { AvailableSheet, SheetModule } from '../model/sheet'
import { SHEETS } from '../sheets/registry'
import { SIZE_NOT_APPLICABLE } from '../sheets/shared/periods'
import { translateValue } from '../model/texts'
import type { CellMap, CellValue, SheetContext, Tone } from '../model/types'
import { carriedLimitations, inputName, isQualified, limitationsOf, type Limitation } from './limits'

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

/**
 * Prüfhinweise der Vorlage in Blattreihenfolge, danach die Hinweise der
 * Webfassung: mit 0 gerechnete Eingaben, Werte ohne Grundlage, eigene Hinweise
 * und – in Blatt 18 und im Bericht – die Einschränkungen des gewählten
 * Verfahrens. Schränkt ein Hinweis in Warnfarbe das Ergebnis ein, erscheint ein
 * bestandener Befund der Würdigung nicht uneingeschränkt grün.
 */
export function buildHints(sheet: AvailableSheet, inputs: CellMap, results: CellMap, context: SheetContext, t: Translate, sheets: readonly SheetModule[] = SHEETS): HintView[] {
  const own = limitationsOf(sheet, inputs, results, context, t)
  const carried = carriedLimitations(sheet, context, t, sheets)
  const qualified = isQualified([...own, ...carried])
  const unfounded = new Set(evaluateSheet(sheet, inputs, context).withoutBasis)
  const template = fieldsOf(sheet.definition)
    .filter((field) => field.type === 'check')
    .flatMap((field): HintView[] => {
      if (field.columns) return strataHints(sheet, field, results, t)
      const value = results[field.cell]
      if (isBlank(value)) return []
      const text = translateValue(sheet.texts, String(value))
      // Nicht uneingeschränkt grün: die Würdigung, sobald ein Hinweis in Warnfarbe das Ergebnis einschränkt, und jeder bestandene Prüfhinweis ohne Grundlage.
      const caveat = toneOf(value) === 'success' && ((qualified && field.alias === 'assessment') || unfounded.has(field.cell))
      return [{ id: field.cell, text: caveat ? `${text} – ${t('qualifiedNote')}` : text, tone: caveat ? 'warning' : toneOf(value), source: 'template' }]
    })
  const limiting = (entries: readonly Limitation[]): HintView[] => entries.filter((entry) => entry.kind !== 'warning' && entry.kind !== 'interpretation').map((entry) => ({ id: entry.id, text: entry.text, tone: entry.tone, source: 'web' }))
  const web = (sheet.webHints?.(inputs, results, context) ?? []).map((hint): HintView => ({ ...hint, text: sheet.texts?.webHints?.[hint.id] ?? hint.text, source: 'web' }))
  return [...template, ...limiting(own), ...web, ...carried.map((entry): HintView => ({ id: entry.id, text: entry.text, tone: entry.tone, source: 'web' }))]
}

/** Warum die Hauptgröße fehlt: TE = AE (Division durch null), ein Text der Vorlage oder die fehlenden Eingaben. */
function primaryNote(sheet: AvailableSheet, inputs: CellMap, context: SheetContext, reason: CellValue, t: Translate, invalid: ReadonlySet<string>): string {
  if (reason === SIZE_NOT_APPLICABLE) return `${t('notDeterminable')} (${t('equalErrors')})`
  if (typeof reason === 'string' && reason) return `${t('notDeterminable')} (${translateValue(sheet.texts, reason)})`
  const named = [...new Set(evaluateSheet(sheet, inputs, context).lacking.get(sheet.definition.summary.primary.cell) ?? [])]
  // Zeigt auch die Vorlage ohne die Eingabe keine Hauptgröße (z. B. Buchwert 0), nennt die Übersicht die ungültigen Eingaben des Blatts.
  const lacking = named.length ? named : [...invalid].filter((cell) => findField(sheet.definition, cell))
  if (lacking.length === 0) return ''
  const names = (list: readonly string[]): string => list.map((input) => inputName(sheet, input)).join('; ')
  const unreadable = lacking.filter((input) => invalid.has(input))
  const missing = lacking.filter((input) => !invalid.has(input))
  // Eine nicht lesbare Eingabe ist ungültig, nicht fehlend.
  const lead = t(unreadable.length ? 'invalidInput' : 'missing')
  return [`${lead}.`, unreadable.length ? t('invalidInputs', { inputs: names(unreadable) }) : '', missing.length ? t('missingInputs', { inputs: names(missing) }) : ''].filter(Boolean).join(' ')
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
export function buildSummary(sheet: AvailableSheet, inputs: CellMap, results: CellMap, context: SheetContext, t: Translate, invalid: ReadonlySet<string> = new Set()): SummaryView {
  const { primary, rows } = sheet.definition.summary
  const value = results[primary.cell] ?? null
  const field = findField(sheet.definition, primary.cell)
  const reason = primary.reason ? results[primary.reason] : null
  // Eine nicht lesbare Eingabe ist eine Angabe: Die Übersicht meldet sie als ungültig, nicht „noch keine Angaben“.
  const empty = invalid.size === 0 && isEmptyForm(sheet, results, context)
  const note = (): string => (empty ? t('noEntries') : primaryNote(sheet, inputs, context, reason ?? null, t, invalid))
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
    // Leeres Formular: keine Prüfhinweise der Vorlage. Ist ein Verfahren gewählt (Blatt 18, Bericht), bleiben die Hinweise der Webfassung in Warnfarbe – etwa, dass aus einer Altvorlage nichts übernommen wird.
    hints: buildHints(sheet, inputs, results, context, t).filter((hint) => !empty || (context.method !== undefined && hint.source === 'web' && hint.tone !== 'neutral' && hint.tone !== 'success')),
  }
}
