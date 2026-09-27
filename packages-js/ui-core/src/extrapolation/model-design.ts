/**
 * Formularteile für den Aufbau der Stichprobe (Leitfaden Kap. 6/7): mehrere
 * Zeiträume (7.3), Gruppen von Programmen (7.8), Teilstichproben je Einheit
 * (7.6, 6.5.3) und die Systembewertung für die Neuberechnung des
 * Konfidenzniveaus (7.7). Eine Teilstichprobe hat im Formular eine
 * Stichprobenschicht und optional vollständig geprüfte Teileinheiten (z. B.
 * den Lead-Partner); deren Buchwert ergibt sich aus dem Buchwert der Einheit.
 */
import type { ExtrapolationDesign, StratumInput, SubsampleEstimator, SubsampleInput, UnitInput } from './types'

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

export interface SubItemRow {
  key: string
  id: string
  bookValue: string
  random: string
  exhaustive: boolean
}

export interface SubsampleRows {
  estimator: SubsampleEstimator
  /** Anzahl der Teileinheiten der Stichprobenschicht (nur Mittelwertschätzung). */
  populationSize: string
  items: readonly SubItemRow[]
}

export const SAMPLED_PART = 'Stichprobe'
export const EXHAUSTIVE_PART = 'Vollerhebung'

export function emptySubItem(key: string): SubItemRow {
  return { key, id: '', bookValue: '', random: '', exhaustive: false }
}

export function emptySubsample(): SubsampleRows {
  return { estimator: 'ratio', populationSize: '', items: [] }
}

/** Aufbau aus vorbelegten Schichten: Zeitraum oder Gruppe gesetzt? */
export function designOf(strata: readonly StratumInput[]): ExtrapolationDesign {
  if (strata.some((stratum) => stratum.period)) return 'periods'
  return strata.some((stratum) => stratum.group) ? 'groups' : 'single'
}

export function stratumPart(stratum: StratumInput): string {
  return stratum.period ?? stratum.group ?? ''
}

type Format = (value: number) => string

/** Formularzeilen einer vorbelegten Teilstichprobe (einstufig, eine Stichprobenschicht). */
export function subsampleRows(sub: SubsampleInput | undefined, format: Format): SubsampleRows | null {
  if (!sub) return null
  const sampled = sub.strata.find((stratum) => stratum.population_size !== undefined)
  return {
    estimator: sub.estimator,
    populationSize: sampled?.population_size === undefined ? '' : String(sampled.population_size),
    items: sub.units.map((unit, index) => ({
      key: `i${index + 1}`,
      id: unit.id,
      bookValue: format(unit.book_value),
      random: unit.random_error ? format(unit.random_error) : '',
      exhaustive: unit.exhaustive ?? false,
    })),
  }
}

/** Zeiträume in der Reihenfolge ihres ersten Auftretens. */
export function periodNames(parts: readonly string[]): string[] {
  return [...new Set(parts.map((part) => part.trim()).filter(Boolean))]
}

function readItems(rows: SubsampleRows, key: string, out: IssueSink): UnitInput[] {
  const seen = new Set<string>()
  return rows.items.map((item, index) => {
    const at = `${key}.items.${index}`
    const id = item.id.trim()
    if (!id) out.flag(`${at}.id`, 'required')
    else if (seen.has(id)) out.flag(`${at}.id`, 'duplicate')
    seen.add(id)
    const unit: UnitInput = {
      id,
      stratum: item.exhaustive ? EXHAUSTIVE_PART : SAMPLED_PART,
      book_value: out.take(`${at}.bookValue`, item.bookValue, { required: true, positive: true }),
      random_error: out.take(`${at}.random`, item.random),
    }
    return item.exhaustive ? { ...unit, exhaustive: true } : unit
  })
}

/** Teilstichprobe für die Anfrage; Buchwert der Stichprobenschicht = Einheit − Vollerhebung. */
export function readSubsample(rows: SubsampleRows, unitBook: number, key: string, out: IssueSink): SubsampleInput {
  const units = readItems(rows, key, out)
  if (!units.some((unit) => !unit.exhaustive)) out.flag(`${key}.items`, 'required')
  const exhaustive = units.filter((unit) => unit.exhaustive).reduce((sum, unit) => sum + unit.book_value, 0)
  const sampled = unitBook - exhaustive
  if (sampled <= 0) out.flag(`${key}.items`, 'range')
  const size = rows.estimator === 'mean_per_unit' ? out.take(`${key}.populationSize`, rows.populationSize, { required: true, positive: true, integer: true }) : undefined
  const strata: StratumInput[] = [{ name: SAMPLED_PART, book_value: sampled, ...(size === undefined ? {} : { population_size: size }) }]
  if (exhaustive > 0) strata.unshift({ name: EXHAUSTIVE_PART, book_value: exhaustive })
  return { estimator: rows.estimator, strata, units }
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
