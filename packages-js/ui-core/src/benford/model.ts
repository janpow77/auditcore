/** Framework-freie Ansichtslogik der Benford-Analyse. */
import type { AnalyseRequest, BenfordCatalogue, BenfordMetricId, BenfordMetricsRequest, BenfordTest, ShortValues } from './types'

export interface AnalyseInput {
  catalogue: BenfordCatalogue
  test: BenfordTest | null
  profile: string | null
  shortValues: ShortValues | null
  values: readonly (number | null)[]
  /** Angeforderte Kennzahlen (bereits ohne abgewählte). */
  metrics?: BenfordMetricsRequest | null
}

export const BENFORD_METRIC_IDS: readonly BenfordMetricId[] = ['chi_square', 'digit_z']

/** Vorgegebene Kennzahlen ohne die abgewählten; `null`, wenn keine übrig bleibt. */
export function activeMetrics(given: BenfordMetricsRequest | null | undefined, disabled: readonly BenfordMetricId[]): BenfordMetricsRequest | null {
  if (!given) return null
  const active: BenfordMetricsRequest = {}
  if (given.chi_square && !disabled.includes('chi_square')) active.chi_square = given.chi_square
  if (given.digit_z && !disabled.includes('digit_z')) active.digit_z = given.digit_z
  return active.chi_square || active.digit_z ? active : null
}

/** Kennungen der vorgegebenen Kennzahlen in fester Reihenfolge (für die Auswahl im Formular). */
export function offeredMetrics(given: BenfordMetricsRequest | null | undefined): BenfordMetricId[] {
  return BENFORD_METRIC_IDS.filter((id) => Boolean(given?.[id]))
}

export type AnalyseError = 'noValues' | 'tooMany' | 'test' | 'profile' | 'shortValues'

export type AnalyseValidation = { ok: true; request: AnalyseRequest } | { ok: false; error: AnalyseError }

/** Zweistellige Tests (erste zwei Ziffern, zweite Ziffer) verlangen eine Regel für kurze Werte. */
export function needsShortValues(catalogue: BenfordCatalogue, test: BenfordTest | null): boolean {
  return catalogue.tests.find((entry) => entry.id === test)?.digits === 2
}

/** Anfrage für `POST /analyze`; Test, Profil und ggf. Regel für kurze Werte sind Pflicht. */
export function buildAnalyseRequest(input: AnalyseInput): AnalyseValidation {
  if (input.values.length === 0) return { ok: false, error: 'noValues' }
  if (input.values.length > input.catalogue.limits.max_values) return { ok: false, error: 'tooMany' }
  if (input.test === null) return { ok: false, error: 'test' }
  if (input.profile === null) return { ok: false, error: 'profile' }
  const twoDigits = needsShortValues(input.catalogue, input.test)
  if (twoDigits && input.shortValues === null) return { ok: false, error: 'shortValues' }
  return {
    ok: true,
    request: {
      test: input.test,
      profile: input.profile,
      values: input.values,
      ...(twoDigits && input.shortValues ? { short_values: input.shortValues } : {}),
      ...(input.metrics ? { metrics: input.metrics } : {}),
    },
  }
}

export type LevelTone = 'neutral' | 'success' | 'accent' | 'warning' | 'danger'

const TONES: readonly LevelTone[] = ['success', 'accent', 'warning', 'danger']

/** Farbton der MAD-Stufe 0–3 (enge … keine Übereinstimmung). */
export function levelTone(level: number): LevelTone {
  return TONES[Math.min(Math.max(level, 0), TONES.length - 1)] ?? 'neutral'
}

/** Anzeige einer Ziffer: zweite Ziffer 0–9, sonst Zahl. */
export function digitLabel(digit: number): string {
  return String(digit)
}
