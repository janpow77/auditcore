/**
 * Anzeige der Ergänzungen nach Leitfaden Kap. 6/7 (reine Funktionen für Vue und
 * React): Zeiträume, Programme einer Gruppe, Teilstichproben, Neuberechnung des
 * Konfidenzniveaus sowie Auswahllisten für Aufbau, Systembewertung und Schätzer.
 */
import type { TableColumn, TableRow } from '@auditcore/common'
import type { Locale } from '../i18n'
import { openSubsample } from './controller-subsample'
import type { ExtrapolationData } from './controller'
import { MAX_SUBSAMPLE_DEPTH, type SubItemRow, type SubStratumRow } from './model-subsample'
import { conclusionLabel, extrapolationAmount, extrapolationConfidenceLabel, extrapolationRate, type ExtrapolationField, type ExtrapolationMetric, type ExtrapolationTranslate } from './view'
import type { EvaluationResult, ExtrapolationCatalogue, ExtrapolationDesign, SubsampleEstimator } from './types'

export interface ExtrapolationChoice<T extends string> {
  id: T
  label: string
}

const DESIGNS: readonly ExtrapolationDesign[] = ['single', 'periods', 'groups']
const ESTIMATORS: readonly SubsampleEstimator[] = ['ratio', 'mean_per_unit', 'pps']

export function extrapolationDesignChoices(catalogue: ExtrapolationCatalogue | null, t: ExtrapolationTranslate): ExtrapolationChoice<ExtrapolationDesign>[] {
  return DESIGNS.map((id) => ({ id, label: catalogue?.designs?.find((entry) => entry.id === id)?.label ?? t(`design${id}`) }))
}

export function subsampleEstimatorChoices(t: ExtrapolationTranslate): ExtrapolationChoice<SubsampleEstimator>[] {
  return ESTIMATORS.map((id) => ({ id, label: t(`estimator${id}`) }))
}

/** Kategorien 1–4 der Systembewertung mit Konfidenzniveau (Tabelle 1, Leitfaden 3.2.1). */
export function systemAssessmentChoices(catalogue: ExtrapolationCatalogue | null, locale: Locale): ExtrapolationChoice<string>[] {
  return (catalogue?.system_assessment ?? []).map((entry) => ({
    id: String(entry.category),
    label: `${entry.category} – ${entry.label} (${extrapolationConfidenceLabel(entry.confidence_level, locale)})`,
  }))
}

export const SUB_ITEM_FIELDS: readonly ExtrapolationField<'id' | 'bookValue' | 'random'>[] = [
  { key: 'id', label: 'subItemId', numeric: false },
  { key: 'bookValue', label: 'bookValue', numeric: true },
  { key: 'random', label: 'randomError', numeric: true },
]

export const SUB_STRATUM_FIELDS: readonly ExtrapolationField<'name' | 'bookValue' | 'populationSize'>[] = [
  { key: 'name', label: 'subStratum', numeric: false },
  { key: 'bookValue', label: 'bookValue', numeric: true },
  { key: 'populationSize', label: 'populationSize', numeric: true },
]

export type SubStratumFieldKey = keyof Pick<SubStratumRow, 'name' | 'bookValue' | 'populationSize'>

/** Ansicht der gerade bearbeiteten Teilstichprobe: Zeilen, Überschrift, Feldpräfix, Stufe. */
export interface SubsampleEditorView {
  rows: NonNullable<ReturnType<typeof openSubsample>>
  title: string
  /** Präfix der Feldbefunde, z. B. `units.2.subsample`. */
  prefix: string
  nested: boolean
  /** Teileinheiten dürfen eine eigene Teilstichprobe haben (nur Stufe 2). */
  allowNested: boolean
}

export function subsampleEditorView(state: ExtrapolationData, t: ExtrapolationTranslate): SubsampleEditorView | null {
  const rows = openSubsample(state)
  const index = state.subsampleUnit
  const unit = index === null ? null : state.form.units[index]
  if (!rows || index === null || !unit) return null
  const unitLabel = unit.id || String(index + 1)
  if (state.subsampleItem === null) {
    return { rows, title: t('subsampleTitle', { unit: unitLabel }), prefix: `units.${index}.subsample`, nested: false, allowNested: MAX_SUBSAMPLE_DEPTH > 1 }
  }
  const item = unit.subsample?.items[state.subsampleItem]
  const itemLabel = item?.id || String(state.subsampleItem + 1)
  return { rows, title: t('subsampleNestedTitle', { unit: unitLabel, item: itemLabel }), prefix: `units.${index}.subsample.items.${state.subsampleItem}.subsample`, nested: true, allowNested: false }
}

export type SubItemFieldKey = keyof Pick<SubItemRow, 'id' | 'bookValue' | 'random'>

const amount = (locale: Locale) => (value: unknown): string => (typeof value === 'number' ? extrapolationAmount(value, locale) : '')
const rate = (locale: Locale) => (value: unknown): string => (typeof value === 'number' ? extrapolationRate(value, locale) : '')

export function periodColumns(t: ExtrapolationTranslate, locale: Locale): TableColumn[] {
  return [
    { key: 'name', label: t('period') },
    { key: 'book_value', label: t('colBookValue'), align: 'end', format: amount(locale) },
    { key: 'projected', label: t('colProjected'), align: 'end', format: amount(locale) },
    { key: 'precision', label: t('colPrecision'), align: 'end', format: (value) => (typeof value === 'number' ? extrapolationAmount(value, locale) : t('notDeterminable')) },
    { key: 'sample_size', label: t('colSampleSize'), align: 'end' },
  ]
}

export function periodRows(result: EvaluationResult): TableRow[] {
  const periods = (result.projection.extra.periods ?? []) as readonly { name: string; book_value: number; projected_random_error: number; precision: number | null; sample_size: number }[]
  return periods.map((entry) => ({ id: entry.name, name: entry.name, book_value: entry.book_value, projected: entry.projected_random_error, precision: entry.precision, sample_size: entry.sample_size }))
}

export function groupColumns(t: ExtrapolationTranslate, locale: Locale): TableColumn[] {
  return [
    { key: 'name', label: t('group') },
    { key: 'observations', label: t('colObservations'), align: 'end' },
    { key: 'projected', label: t('colProjected'), align: 'end', format: amount(locale) },
    { key: 'ter', label: t('colTer'), align: 'end', format: rate(locale) },
    { key: 'upper', label: t('colUpper'), align: 'end', format: (value) => (typeof value === 'number' ? extrapolationRate(value, locale) : t('notDeterminable')) },
    { key: 'conclusion', label: t('colConclusion') },
  ]
}

export function groupRows(result: EvaluationResult, catalogue: ExtrapolationCatalogue | null): TableRow[] {
  return (result.groups ?? []).map((group) => ({
    id: group.name,
    name: group.name,
    observations: group.observations,
    projected: group.total_error_rate.projected_random_error,
    ter: group.total_error_rate.rate,
    upper: group.total_error_rate.upper_limit_rate,
    conclusion: conclusionLabel(catalogue, group.total_error_rate.conclusion),
  }))
}

export function subsampleColumns(t: ExtrapolationTranslate, locale: Locale): TableColumn[] {
  return [
    { key: 'unit', label: t('unitId') },
    { key: 'estimator', label: t('estimator') },
    { key: 'book_value', label: t('colBookValue'), align: 'end', format: amount(locale) },
    { key: 'projected', label: t('colProjected'), align: 'end', format: amount(locale) },
    { key: 'rate', label: t('colRate'), align: 'end', format: rate(locale) },
    { key: 'coverage', label: t('colCoverage'), align: 'end', format: rate(locale) },
    { key: 'items', label: t('colItems'), align: 'end' },
  ]
}

export function subsampleResultRows(result: EvaluationResult, t: ExtrapolationTranslate): TableRow[] {
  return (result.subsamples ?? []).map((entry, index) => ({
    id: `${entry.unit_id}-${index}`,
    unit: entry.unit_id,
    estimator: t(`estimator${entry.estimator}`),
    book_value: entry.book_value,
    projected: entry.projected_error,
    rate: entry.error_rate,
    coverage: entry.coverage,
    items: entry.sampled_items + entry.exhaustive_items,
  }))
}

/** Hinweise aus Gruppen und Teilstichproben (die der Hochrechnung stehen im Ergebnis). */
export function detailWarnings(result: EvaluationResult): string[] {
  return [...(result.groups ?? []).flatMap((group) => group.warnings), ...(result.subsamples ?? []).flatMap((entry) => entry.warnings)]
}

export interface RecalculationView {
  metrics: ExtrapolationMetric[]
  verdict: string
}

/** Neuberechnung des Konfidenzniveaus; `null`, wenn nicht anwendbar (Ergebnis schlüssig usw.). */
export function recalculationView(result: EvaluationResult, t: ExtrapolationTranslate, locale: Locale): RecalculationView | null {
  const recalculation = result.confidence_recalculation
  if (!recalculation?.applicable || recalculation.confidence_level === null) return null
  const metrics: ExtrapolationMetric[] = [
    { id: 'recalc-level', label: t('recalcLevel'), value: extrapolationRate(recalculation.confidence_level, locale) },
    { id: 'recalc-z', label: t('recalcCoefficient'), value: (recalculation.recalculated_coefficient ?? 0).toLocaleString(locale, { maximumFractionDigits: 3 }) },
  ]
  if (recalculation.required_level !== null) {
    metrics.push({ id: 'recalc-required', label: t('recalcRequired'), value: extrapolationConfidenceLabel(recalculation.required_level, locale) })
  }
  const verdict = recalculation.supports_not_material === null ? t('recalcNoRequirement') : t(recalculation.supports_not_material ? 'recalcSupports' : 'recalcNotSupported')
  return { metrics, verdict }
}

/** Gibt es Ergänzungen anzuzeigen? */
export function hasExtrapolationDetails(result: EvaluationResult): boolean {
  return periodRows(result).length > 0 || (result.groups?.length ?? 0) > 0 || (result.subsamples?.length ?? 0) > 0 || result.confidence_recalculation?.applicable === true
}
