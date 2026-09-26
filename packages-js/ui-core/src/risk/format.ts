/** Anzeigeformate und Beschriftungen der Risiko-Merkmale (framework-frei). */
import { intlFormatNumber as formatNumber, intlFormatPercent as formatPercent } from '@auditcore/common'
import type { Locale } from '../i18n'
import type { JsonValue } from './types'
import type { FlagState } from './state'

/** Farbton wie `FaBadge` (`tone`). */
export type Tone = 'neutral' | 'accent' | 'success' | 'warning' | 'danger'

/** Wert eines Eingabefelds: leer ausdrücklich, Zahlen im Sprachformat. */
const BOOLEAN_TEXT: Readonly<Record<Locale, readonly [string, string]>> = { de: ['ja', 'nein'], en: ['yes', 'no'] }

function formatBoolean(value: boolean, locale: Locale): string {
  const [yes, no] = BOOLEAN_TEXT[locale]
  return value ? yes : no
}

export function formatValue(value: JsonValue | undefined, locale: Locale, empty: string): string {
  if (value === null || value === undefined || value === '') return empty
  if (typeof value === 'number') return formatNumber(value, locale, { maximumFractionDigits: 4 })
  if (typeof value === 'boolean') return formatBoolean(value, locale)
  if (Array.isArray(value)) return value.map((item) => formatValue(item, locale, empty)).join('; ')
  if (typeof value === 'object') return JSON.stringify(value)
  return value
}

export function formatShare(share: number, locale: Locale): string {
  return formatPercent(share, locale, 1)
}

export function formatAmount(value: number | null, locale: Locale): string {
  return value === null ? '' : formatNumber(value, locale, { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

const SEVERITY_TONES: Readonly<Record<string, Tone>> = {
  CRITICAL: 'danger',
  HIGH: 'danger',
  MEDIUM: 'warning',
  LOW: 'accent',
  INFO: 'neutral',
}

export function severityTone(severity: string | null): Tone {
  return severity ? (SEVERITY_TONES[severity] ?? 'neutral') : 'neutral'
}

/** Symbol je Zustand: Farbe ist nie der einzige Träger der Bedeutung. */
export const STATE_ICONS: Readonly<Record<FlagState, string>> = {
  hit: '!',
  undetermined: '?',
  clear: '–',
  skipped: '⤼',
  absent: '·',
}

export function stateTone(state: FlagState): Tone {
  if (state === 'hit') return 'danger'
  if (state === 'undetermined') return 'warning'
  return 'neutral'
}

/** Bekannte Parameter der Regelarten; unbekannte behalten ihren Schlüssel. */
const PARAMETER_LABELS: Readonly<Record<string, { de: string; en: string }>> = {
  multiple: { de: 'glattes Vielfaches von', en: 'round multiple of' },
  amount_gt: { de: 'Betrag größer als', en: 'amount greater than' },
  'thresholds.static': { de: 'Wertgrenzen', en: 'value limits' },
  'lower.proximity': { de: 'Nähe unter der Schwelle (Anteil)', en: 'proximity below threshold (share)' },
  threshold: { de: 'Schwelle', en: 'threshold' },
  value: { de: 'Vergleichswert', en: 'comparison value' },
  ratio_gt: { de: 'Quote größer als', en: 'ratio greater than' },
  rate_gt: { de: 'Quote größer als (%)', en: 'rate greater than (%)' },
  total_min: { de: 'Mindestanzahl', en: 'minimum count' },
  min_length: { de: 'Mindestlänge', en: 'minimum length' },
  'group.cases_gt': { de: 'Gruppe: Vorhaben mehr als', en: 'group: cases more than' },
  'group.sum_gt': { de: 'Gruppe: Summe größer als', en: 'group: sum greater than' },
  'pair.count_gt': { de: 'Paar: Belege mehr als', en: 'pair: records more than' },
  'pair.sum_gt': { de: 'Paar: Summe größer als', en: 'pair: sum greater than' },
  share_gte: { de: 'Anteil mindestens', en: 'share at least' },
}

export function parameterLabel(key: string, locale: Locale): string {
  const label = PARAMETER_LABELS[key]
  return label ? label[locale] : key
}
