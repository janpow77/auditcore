/**
 * Anzeige des Stichprobenrechners für Vue und React (reine Funktionen):
 * Einheiten, Fehlermeldungen der Felder, Methodengruppen, Tabellenspalten,
 * Zusammenfassungen. Texte kommen ausschließlich aus `samplingMessages`.
 */
import { intlFormatNumber as formatNumber, intlFormatPercent as formatPercent, type TableColumn, type TableRow } from '@auditcore/common'
import type { BadgeTone } from '../base/types'
import type { Locale, Translate } from '../i18n'
import type { SamplingMessageKey } from './messages'
import { isPercent, positiveSum, strataOf, type FieldError } from './model'
import type { ConfidenceLevel, MethodProfile, ParameterSpec, PopulationItem, SamplingCatalogue, SelectionResult, SizeResult } from './types'
import type { SelectionError } from './controller'

export type SamplingTranslate = Translate<SamplingMessageKey>

/** Einheit hinter dem Eingabefeld (Prozent, Euro oder keine). */
export function parameterUnit(spec: ParameterSpec): string {
  if (isPercent(spec)) return '%'
  return spec.unit === 'EUR' ? '€' : ''
}

function rangeText(error: FieldError, t: SamplingTranslate, locale: Locale): string {
  const fmt = (value: number): string => formatNumber(value, locale, { maximumFractionDigits: 4 })
  if (error.min !== undefined && error.max !== undefined) return t('rangeBetween', { min: fmt(error.min), max: fmt(error.max) })
  if (error.min !== undefined) return t('rangeFrom', { min: fmt(error.min) })
  return t('rangeTo', { max: fmt(error.max ?? 0) })
}

/** Fehlermeldung eines Eingabefelds, leer ohne Fehler. */
export function samplingFieldError(error: FieldError | undefined, t: SamplingTranslate, locale: Locale): string {
  if (!error) return ''
  if (error.code === 'range') return t('errorRange', { range: rangeText(error, t, locale) })
  return error.code === 'required' ? t('errorRequired') : t('errorInvalid')
}

export function selectionErrorKey(error: SelectionError): SamplingMessageKey {
  return `selectionError${error}`
}

export function confidenceText(level: ConfidenceLevel, t: SamplingTranslate, locale: Locale): string {
  return t('confidenceOption', { level: formatPercent(level.level, locale, 0), factor: formatNumber(level.factor, locale, { maximumFractionDigits: 3 }) })
}

export interface MethodGroup {
  kind: 'mus' | 'srs'
  label: string
  methods: MethodProfile[]
}

export function methodGroups(catalogue: SamplingCatalogue): MethodGroup[] {
  return [
    { kind: 'mus', label: 'MUS', methods: catalogue.methods.filter((method) => method.kind === 'mus') },
    { kind: 'srs', label: 'SRS', methods: catalogue.methods.filter((method) => method.kind === 'srs') },
  ]
}

export function methodTone(profile: MethodProfile | null): BadgeTone {
  const status = profile?.status
  return status === 'RECOMMENDED' ? 'success' : status === 'SUPERSEDED' ? 'warning' : 'neutral'
}

export function methodStatusKey(profile: MethodProfile): SamplingMessageKey {
  return `status${profile.status}`
}

/** Zusammenfassung der Grundgesamtheit; leer, wenn keine Elemente vorliegen. */
export function populationText(items: readonly PopulationItem[], t: SamplingTranslate, locale: Locale): string {
  if (items.length === 0) return ''
  const summary = t('populationCount', { count: formatNumber(items.length, locale), sum: formatNumber(positiveSum(items), locale, { maximumFractionDigits: 2 }) })
  const strata = strataOf(items).length
  return strata ? `${summary} · ${t('strataCount', { count: strata })}` : summary
}

const numberFormat = (locale: Locale) => (value: unknown): string =>
  typeof value === 'number' ? formatNumber(value, locale, { maximumFractionDigits: 4 }) : ''
const amountFormat = (locale: Locale) => (value: unknown): string =>
  typeof value === 'number' ? formatNumber(value, locale, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : ''
const plain = (value: unknown): string => (value === null || value === undefined ? '' : String(value))

export function derivationColumns(t: SamplingTranslate, locale: Locale): TableColumn[] {
  return [
    { key: 'label', label: t('step') },
    { key: 'formula', label: t('stepFormula') },
    { key: 'value', label: t('stepValue'), align: 'end', format: numberFormat(locale) },
  ]
}

export function derivationRows(result: SizeResult): TableRow[] {
  return result.derivation.map((step, index) => ({ id: index, ...step }))
}

export function sizeTexts(result: SizeResult, t: SamplingTranslate, locale: Locale): { size: string; interval: string } {
  return {
    size: t('resultSummary', { size: formatNumber(result.sample_size, locale) }),
    interval: result.kind === 'mus' ? t('interval', { interval: formatNumber(result.interval, locale, { maximumFractionDigits: 2 }) }) : '',
  }
}

export function selectionColumns(result: SelectionResult, t: SamplingTranslate, locale: Locale): TableColumn[] {
  const stratified = result.strata.some((stratum) => stratum.stratum !== null)
  return [
    { key: 'order', label: t('colOrder'), align: 'end', sortable: true },
    { key: 'position', label: t('colPosition'), align: 'end', sortable: true },
    { key: 'id', label: t('colId'), sortable: true },
    { key: 'value', label: t('colValue'), align: 'end', sortable: true, format: amountFormat(locale) },
    ...(stratified ? [{ key: 'stratum', label: t('colStratum'), sortable: true, format: plain }] : []),
    ...(result.method === 'mus' ? [{ key: 'hits', label: t('colHits'), align: 'end' as const }] : []),
  ]
}

export function strataColumns(result: SelectionResult, t: SamplingTranslate, locale: Locale): TableColumn[] {
  const amount = amountFormat(locale)
  return [
    { key: 'stratum', label: t('stratum'), format: (value) => (value === null ? t('noStratum') : String(value)) },
    { key: 'population', label: t('stratumPopulation'), align: 'end' },
    { key: 'sample_size', label: t('stratumSample'), align: 'end' },
    ...(result.method === 'mus'
      ? [
          { key: 'interval', label: t('stratumInterval'), align: 'end' as const, format: amount },
          { key: 'start', label: t('stratumStart'), align: 'end' as const, format: amount },
        ]
      : []),
  ]
}

export function strataRows(result: SelectionResult): TableRow[] {
  return result.strata.map((stratum, index) => ({ id: index, ...stratum }))
}

export function selectionRows(result: SelectionResult): TableRow[] {
  return result.rows.map((row) => ({ ...row }))
}

/** Hinweise auf Elemente außerhalb der Auswahlbasis. */
export function excludedLines(result: SelectionResult, t: SamplingTranslate): string[] {
  return result.strata.flatMap((stratum) => [
    ...(stratum.excluded_negative?.length ? [t('excludedNegative', { ids: stratum.excluded_negative.join(', ') })] : []),
    ...(stratum.excluded_zero_or_missing?.length ? [t('excludedZero', { ids: stratum.excluded_zero_or_missing.join(', ') })] : []),
  ])
}

export interface SelectionTexts {
  seed: string
  origin: string
  summary: string
  reproducible: string
}

export function selectionTexts(result: SelectionResult, t: SamplingTranslate, locale: Locale): SelectionTexts {
  return {
    seed: t('seedUsed', { seed: result.seed }),
    origin: result.seed_generated ? t('seedGenerated') : t('seedGiven'),
    summary: t('selectedSummary', { selected: formatNumber(result.selected, locale), population: formatNumber(result.population, locale) }),
    reproducible: t('reproducible', { hash: result.items_sha256.slice(0, 12) }),
  }
}

/** Zahlformat der Eingabefelder (ohne Tausendertrennung, bis 6 Nachkommastellen). */
export function samplingInputNumber(locale: Locale): (value: number) => string {
  return (value) => formatNumber(value, locale, { maximumFractionDigits: 6, useGrouping: false })
}
