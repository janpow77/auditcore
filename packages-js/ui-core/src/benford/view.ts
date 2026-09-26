/**
 * Anzeige der Benford-Analyse für Vue und React (reine Funktionen): Kennzahlen,
 * Diagrammbeschriftungen und Spalten der Zifferntabelle. Texte ausschließlich
 * aus `benfordMessages`.
 */
import { intlFormatNumber as formatNumber, intlFormatPercent as formatPercent, type TableColumn, type TableRow } from '@flowaudit/common'
import type { Locale, Translate } from '../i18n'
import type { BenfordMessageKey } from './messages'
import type { AnalyseError } from './model'
import type { BenfordAnalysis, Conformity, ConformityProfile } from './types'

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
