/**
 * Formularteile für den Aufbau der Stichprobe (Leitfaden Kap. 6/7): mehrere
 * Zeiträume (7.3), Gruppen von Programmen (7.8), Teilstichproben je Einheit
 * (7.6, 6.5.3) und die Systembewertung für die Neuberechnung des
 * Konfidenzniveaus (7.7). Teilstichproben: `model-subsample.ts`.
 */
import type { ExtrapolationDesign, StratumInput } from './types'

export type DesignIssue = 'required' | 'invalid' | 'range' | 'reason' | 'stratum' | 'duplicate'

export interface DesignRule {
  required?: boolean
  positive?: boolean
  integer?: boolean
  max?: number
}

/** Sammelt Feldbefunde (von `model.ts` bereitgestellt). */
export interface IssueSink {
  take(key: string, text: string, rule?: DesignRule): number
  flag(key: string, issue: DesignIssue): void
}

/** Aufbau aus vorbelegten Schichten: Zeitraum oder Gruppe gesetzt? */
export function designOf(strata: readonly StratumInput[]): ExtrapolationDesign {
  if (strata.some((stratum) => stratum.period)) return 'periods'
  return strata.some((stratum) => stratum.group) ? 'groups' : 'single'
}

export function stratumPart(stratum: StratumInput): string {
  return stratum.period ?? stratum.group ?? ''
}


/** Zeiträume in der Reihenfolge ihres ersten Auftretens. */
export function periodNames(parts: readonly string[]): string[] {
  return [...new Set(parts.map((part) => part.trim()).filter(Boolean))]
}

/** Ergänzungen der Anfrage je Aufbau (Zeitraumliste, Zahl der Einheiten, Systembewertung). */
export function designRequest(design: ExtrapolationDesign, parts: readonly string[], populationUnits: string, systemAssessment: string, out: IssueSink) {
  const units = design === 'periods' && populationUnits.trim() ? out.take('populationUnits', populationUnits, { positive: true, integer: true }) : undefined
  return {
    ...(design === 'periods' ? { periods: periodNames(parts).map((name) => ({ name })) } : {}),
    ...(units === undefined ? {} : { population_units: units }),
    ...(systemAssessment ? { system_assessment: Number(systemAssessment) } : {}),
  }
}

/** Schlüssel einer Schicht für die Zuordnung der Einheiten (je Zeitraum eindeutig). */
export function stratumKey(design: ExtrapolationDesign, part: string, name: string): string {
  return design === 'periods' ? `${part.trim()}\u0000${name.trim()}` : name.trim()
}
