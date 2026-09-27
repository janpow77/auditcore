/**
 * Anzeige der Benford-Analyse für Vue und React (reine Funktionen): Kennzahlen,
 * Diagrammbeschriftungen und Spalten der Zifferntabelle. Texte ausschließlich
 * aus `benfordMessages`.
 */
import { intlFormatNumber as formatNumber, intlFormatPercent as formatPercent, type TableColumn, type TableRow } from '@auditcore/common'
import type { Locale, Translate } from '../i18n'
import type { BenfordMessageKey } from './messages'
import type { AnalyseError } from './model'
import type { BenfordAnalysis, BenfordMetricId, ChiSquareMetric, Conformity, ConformityProfile, DigitZMetric } from './types'

export type BenfordTranslate = Translate<BenfordMessageKey>

export function analyseErrorKey(error: AnalyseError): BenfordMessageKey {
  return `error${error}`
}

export function benfordValuesText(count: number, t: BenfordTranslate, locale: Locale): string {
  return count ? t('valuesCount', { count: formatNumber(count, locale) }) : t('valuesEmpty')
}

/** Titel eines Balkens (Tooltip und Vorlesetext). */
export function benfordBarTitle(conformity: Conformity, index: number, t: BenfordTranslate, locale: Locale): string {
  const row = conformity.rows[index]
  if (!row) return ''
  return t('barTitle', {
    digit: row.digit,
    observed: formatPercent(row.observed_share, locale, 2),
    expected: formatPercent(row.expected_share, locale, 2),
    z: formatNumber(row.z, locale, { maximumFractionDigits: 2 }),
  })
}

export function benfordChartTitle(conformity: Conformity, testLabel: string, t: BenfordTranslate): string {
  return t('chartLabel', { test: testLabel, count: conformity.exceeding_digits.length })
}

export function benfordTickText(value: number, digits: number, locale: Locale): string {
  return formatPercent(value, locale, digits)
}

export interface BenfordMetricTexts {
  analysed: string
  excluded: string
  excludedDetail: string
  mad: string
  madBounds: string
  chi2: string
  chi2Detail: string
  chi2Verdict: string
  zDigits: string
  exceeding: string
}

export function benfordMetricTexts(analysis: BenfordAnalysis, profile: ConformityProfile | null, t: BenfordTranslate, locale: Locale): BenfordMetricTexts {
  const number = (value: number, digits = 4): string => formatNumber(value, locale, { maximumFractionDigits: digits })
  const { conformity, distribution } = analysis
  const excluded = distribution.excluded
  const bounds = (profile?.mad_bounds[conformity.test] ?? []).map((bound) => number(bound)).join(' / ')
  const p = conformity.p_value < 0.0001 ? `< ${number(0.0001)}` : `= ${number(conformity.p_value, 4)}`
  return {
    analysed: formatNumber(conformity.analysed, locale),
    excluded: formatNumber(excluded.zero + excluded.missing + excluded.short, locale),
    excludedDetail: t('excludedDetail', { zero: excluded.zero, missing: excluded.missing, short: excluded.short, negative: distribution.negative_absolute }),
    mad: number(conformity.mad, 5),
    madBounds: t('madBounds', { bounds }),
    chi2: number(conformity.chi2_statistic, 2),
    chi2Detail: t('chi2Detail', { dof: conformity.degrees_of_freedom, p }),
    chi2Verdict: t(conformity.chi2_exceeds ? 'chi2Exceeds' : 'chi2Within', { alpha: number(conformity.significance_level, 3) }),
    zDigits: t('zDigits', { critical: number(conformity.z_critical, 2) }),
    exceeding: conformity.exceeding_digits.length ? conformity.exceeding_digits.join(', ') : t('zNone'),
  }
}

export function benfordDigitColumns(t: BenfordTranslate, locale: Locale): TableColumn[] {
  const share = (value: unknown): string => (typeof value === 'number' ? formatPercent(value, locale, 2) : '')
  const signedShare = (value: unknown): string => (typeof value === 'number' ? `${value > 0 ? '+' : ''}${formatPercent(value, locale, 2)}` : '')
  const decimal = (value: unknown): string =>
    typeof value === 'number' ? formatNumber(value, locale, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : ''
  return [
    { key: 'digit', label: t('colDigit'), align: 'end', sortable: true },
    { key: 'observed_count', label: t('colCount'), align: 'end', sortable: true },
    { key: 'observed_share', label: t('colObserved'), align: 'end', sortable: true, format: share },
    { key: 'expected_share', label: t('colExpected'), align: 'end', format: share },
    { key: 'deviation', label: t('colDeviation'), align: 'end', sortable: true, format: signedShare },
    { key: 'z', label: t('colZ'), align: 'end', sortable: true, format: decimal },
    { key: 'exceeds', label: t('colExceeds'), align: 'center', format: (value) => (value === true ? t('yes') : '') },
  ]
}

export function benfordDigitRows(conformity: Conformity): TableRow[] {
  return conformity.rows.map((row) => ({ id: row.digit, ...row }))
}

export function benfordMetricLabel(id: BenfordMetricId, t: BenfordTranslate): string {
  return t(`metric${id}`)
}

export interface BenfordChiTexts {
  statistic: string
  detail: string
  critical: string
  verdict: string
  /** Farbton des Urteils: `warning` (verworfen), `success`, `neutral` (ohne Niveau). */
  tone: 'warning' | 'success' | 'neutral'
}

export interface BenfordDigitZTexts {
  digits: string
  detail: string
  largest: string
}

function pText(p: number, number: (value: number, digits?: number) => string): string {
  return p < 0.0001 ? `< ${number(0.0001)}` : `= ${number(p, 4)}`
}

/** Texte der Kennzahl `chi_square` (kritische Werte je Niveau, Urteil nur mit Niveau). */
export function benfordChiTexts(metric: ChiSquareMetric, t: BenfordTranslate, locale: Locale): BenfordChiTexts {
  const number = (value: number, digits = 4): string => formatNumber(value, locale, { maximumFractionDigits: digits })
  const values = metric.critical_values.map((entry) => t('criticalValue', { alpha: number(entry.level, 3), value: number(entry.value, 3) })).join(' · ')
  const alpha = metric.significance_level === null ? '' : number(metric.significance_level, 3)
  const verdict = metric.rejects === null ? t('chiNoLevel') : t(metric.rejects ? 'chiRejects' : 'chiKeeps', { alpha })
  return {
    statistic: number(metric.chi2_statistic, 2),
    detail: t('chiTestDetail', { dof: metric.degrees_of_freedom, p: pText(metric.p_value, number) }),
    critical: t('criticalValues', { values }),
    verdict,
    tone: metric.rejects === null ? 'neutral' : metric.rejects ? 'warning' : 'success',
  }
}

/** Texte der Kennzahl `digit_z` („auffällige Ziffern“ nur mit kritischem z-Wert). */
export function benfordDigitZTexts(metric: DigitZMetric, t: BenfordTranslate, locale: Locale): BenfordDigitZTexts {
  const number = (value: number, digits: number): string => formatNumber(value, locale, { maximumFractionDigits: digits })
  const correction = t(metric.continuity_correction ? 'withCorrection' : 'withoutCorrection')
  const exceeding = metric.exceeding_digits
  const largest = metric.rows.reduce<DigitZMetric['rows'][number] | null>((top, row) => (top === null || row.z > top.z ? row : top), null)
  return {
    digits: exceeding === null ? t('digitZNoLimit') : exceeding.length ? exceeding.join(', ') : t('zNone'),
    detail: metric.z_critical === null ? correction : t('digitZDetail', { critical: number(metric.z_critical, 3), correction }),
    largest: largest ? t('digitZValues', { digit: largest.digit, z: number(largest.z, 2) }) : '',
  }
}
