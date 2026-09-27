import { intlFormatNumber as formatNumber, intlFormatPercent as formatPercent } from '@auditcore/common'
import type { Locale, Translate } from '../i18n'
import type { SamplesizeData } from './controller'
import type { SamplesizeMessageKey } from './messages'
import { CHOICE_FIELDS, methodById, PERCENT_FIELDS, scalarFields, strataColumns, type StratumColumn } from './model'
import type { SampleSizeCatalogue, SampleSizeMethod, SampleSizePlan } from './types'

type T = Translate<SamplesizeMessageKey>

export interface SamplesizeOption {
  value: string
  label: string
}

/** Ein Eingabefeld, wie Vue und React es darstellen. */
export interface SamplesizeFieldView {
  key: string
  label: string
  kind: 'choice' | 'number'
  options: SamplesizeOption[]
  value: string
  issue: string | null
  inputMode: 'decimal' | 'numeric'
}

export interface SamplesizeCell {
  key: string
  text: string
}

export function samplesizeMethod(state: SamplesizeData): SampleSizeMethod | null {
  return methodById(state.catalogue, state.form.methodId)
}

function levels(catalogue: SampleSizeCatalogue, method: SampleSizeMethod, locale: Locale): SamplesizeOption[] {
  const table = method.confidence_table === 'reliability' ? catalogue.tables.reliability : catalogue.tables.z
  return [...table].sort((a, b) => a.level - b.level).map((row) => ({ value: String(row.level), label: formatPercent(row.level, locale) }))
}

function options(field: string, catalogue: SampleSizeCatalogue, method: SampleSizeMethod, locale: Locale, t: T): SamplesizeOption[] {
  const choices = (rows: readonly { id: string; label: string }[]) => rows.map((row) => ({ value: row.id, label: row.label }))
  if (field === 'confidence_level') return levels(catalogue, method, locale)
  if (field === 'factor_profile') return choices(catalogue.factor_profiles)
  if (field === 'rule') return choices(catalogue.nonstatistical_rules)
  return [{ value: '', label: t('optional') }, ...choices(catalogue.assurance_levels)]
}

/** Eingabefelder der gewählten Methode mit Beschriftung, Auswahl und Fehlermeldung. */
export function samplesizeFields(state: SamplesizeData, t: T, locale: Locale): SamplesizeFieldView[] {
  const method = samplesizeMethod(state)
  const catalogue = state.catalogue
  if (!method || !catalogue) return []
  return scalarFields(method).map((key) => {
    const choice = CHOICE_FIELDS.includes(key)
    const issue = state.issues[key]
    return {
      key,
      label: t(key as SamplesizeMessageKey),
      kind: choice ? 'choice' : 'number',
      options: choice ? options(key, catalogue, method, locale, t) : [],
      value: state.form.values[key] ?? '',
      issue: issue ? t(issue) : null,
      inputMode: key === 'population_size' ? 'numeric' : 'decimal',
    }
  })
}

const COLUMN_LABELS: Record<StratumColumn, SamplesizeMessageKey> = {
  name: 'stratumName',
  populationSize: 'stratumPopulation',
  bookValue: 'stratumBookValue',
  sd: 'stratumSd',
  exhaustive: 'stratumExhaustive',
}

export function samplesizeStrataColumns(state: SamplesizeData, t: T): { key: StratumColumn; label: string }[] {
  return strataColumns(samplesizeMethod(state)).map((key) => ({ key, label: t(COLUMN_LABELS[key]) }))
}

/** Zahl für die Anzeige: ganze Beträge gruppiert, kleine Werte mit bis zu sechs Stellen. */
export function samplesizeNumber(value: number, locale: Locale): string {
  return formatNumber(value, locale, { maximumFractionDigits: Math.abs(value) < 10 ? 6 : 2 })
}

export function samplesizeSummary(plan: SampleSizePlan, t: T, locale: Locale): SamplesizeCell[] {
  const rows: SamplesizeCell[] = [
    { key: t('sampleSize'), text: formatNumber(plan.sample_size, locale) },
    { key: t('rawSize'), text: samplesizeNumber(plan.raw_size, locale) },
  ]
  if (plan.interval !== null) rows.push({ key: t('interval'), text: `${samplesizeNumber(plan.interval, locale)} €` })
  return rows
}

export function samplesizeAllocation(plan: SampleSizePlan, t: T, locale: Locale): string[][] {
  return plan.strata.map((row) => [
    row.name,
    formatNumber(row.sample_size, locale),
    row.share === null ? '–' : formatPercent(row.share, locale, 1),
    row.cut_off === null ? '–' : `${samplesizeNumber(row.cut_off, locale)} €`,
    row.exhaustive ? t('yes') : t('no'),
  ])
}

export function samplesizeDerivation(plan: SampleSizePlan, locale: Locale): string[][] {
  return plan.derivation.map((step) => [step.label, step.formula, samplesizeNumber(step.value, locale), step.source])
}

/** Anteile werden in Prozent erfasst (Beschriftung „(%)“). */
export const samplesizePercentFields = PERCENT_FIELDS
