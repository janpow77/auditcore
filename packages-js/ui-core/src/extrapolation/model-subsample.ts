/**
 * Teilstichproben im Formular (Leitfaden 7.6, 6.4.10, 6.5.3): Fehler einer
 * Einheit aus einer Zufallsauswahl ihrer Belege, Zahlungsanträge oder
 * Projektpartner.
 *
 * Ohne eigene Teilschichten gilt die einfache Form: eine Stichprobenschicht
 * und vollständig geprüfte Teileinheiten (z. B. der Lead-Partner); der
 * Buchwert der Stichprobenschicht ist der Buchwert der Einheit abzüglich der
 * Vollerhebung. Mit Teilschichten werden Buchwert und Anzahl je Teilschicht
 * erfasst und jede Teileinheit einer Teilschicht zugeordnet. Eine Teileinheit
 * darf selbst eine Teilstichprobe haben (dreistufig, 6.5.3.2.2), tiefer nicht.
 */
import type { IssueSink } from './model-design'
import type { StratumInput, SubsampleEstimator, SubsampleInput, UnitInput } from './types'

export const SAMPLED_PART = 'Stichprobe'
export const EXHAUSTIVE_PART = 'Vollerhebung'
/** Einheit (Stufe 1) → Teileinheit (Stufe 2) → Teileinheit (Stufe 3). */
export const MAX_SUBSAMPLE_DEPTH = 2

export interface SubStratumRow {
  key: string
  name: string
  bookValue: string
  populationSize: string
}

export interface SubItemRow {
  key: string
  id: string
  /** Teilschicht (nur mit eigenen Teilschichten). */
  stratum: string
  bookValue: string
  random: string
  exhaustive: boolean
  /** Teilstichprobe der Teileinheit (dreistufig). */
  subsample: SubsampleRows | null
}

export interface SubsampleRows {
  estimator: SubsampleEstimator
  /** Anzahl Teileinheiten der Stichprobenschicht (einfache Form, Mittelwertschätzung). */
  populationSize: string
  /** Eigene Teilschichten; leer = einfache Form. */
  strata: readonly SubStratumRow[]
  items: readonly SubItemRow[]
}

export function emptySubItem(key: string, stratum = ''): SubItemRow {
  return { key, id: '', stratum, bookValue: '', random: '', exhaustive: false, subsample: null }
}

export function emptySubStratum(key: string): SubStratumRow {
  return { key, name: '', bookValue: '', populationSize: '' }
}

export function emptySubsample(): SubsampleRows {
  return { estimator: 'ratio', populationSize: '', strata: [], items: [] }
}

type Format = (value: number) => string

function isSimple(sub: SubsampleInput): boolean {
  return sub.strata.every((stratum) => stratum.name === SAMPLED_PART || stratum.name === EXHAUSTIVE_PART)
}

/** Formularzeilen einer vorbelegten Teilstichprobe (einfache Form oder mit Teilschichten). */
export function subsampleRows(sub: SubsampleInput | undefined, format: Format, prefix = 'i'): SubsampleRows | null {
  if (!sub) return null
  const simple = isSimple(sub)
  const sampled = sub.strata.find((stratum) => stratum.name === SAMPLED_PART)
  return {
    estimator: sub.estimator,
    populationSize: simple && sampled?.population_size !== undefined ? String(sampled.population_size) : '',
    strata: simple ? [] : sub.strata.map((stratum, index) => ({
      key: `${prefix}s${index + 1}`,
      name: stratum.name,
      bookValue: format(stratum.book_value),
      populationSize: stratum.population_size === undefined ? '' : String(stratum.population_size),
    })),
    items: sub.units.map((unit, index) => ({
      key: `${prefix}${index + 1}`,
      id: unit.id,
      stratum: simple ? '' : unit.stratum,
      bookValue: format(unit.book_value),
      random: unit.random_error ? format(unit.random_error) : '',
      exhaustive: unit.exhaustive ?? false,
      subsample: subsampleRows(unit.subsample, format, `${prefix}${index + 1}.`),
    })),
  }
}

function readItem(item: SubItemRow, at: string, simple: boolean, depth: number, out: IssueSink): UnitInput {
  const book = out.take(`${at}.bookValue`, item.bookValue, { required: true, positive: true })
  const stratum = simple ? (item.exhaustive ? EXHAUSTIVE_PART : SAMPLED_PART) : item.stratum.trim()
  const nested = item.subsample && depth < MAX_SUBSAMPLE_DEPTH ? item.subsample : null
  const unit: UnitInput = {
    id: item.id.trim(),
    stratum,
    book_value: book,
    ...(nested ? { subsample: readSubsample(nested, book, `${at}.subsample`, out, depth + 1) } : { random_error: out.take(`${at}.random`, item.random) }),
  }
  return item.exhaustive ? { ...unit, exhaustive: true } : unit
}

function readItems(rows: SubsampleRows, key: string, depth: number, out: IssueSink): UnitInput[] {
  const seen = new Set<string>()
  const names = new Set(rows.strata.map((stratum) => stratum.name.trim()))
  const simple = rows.strata.length === 0
  return rows.items.map((item, index) => {
    const at = `${key}.items.${index}`
    const id = item.id.trim()
    if (!id) out.flag(`${at}.id`, 'required')
    else if (seen.has(id)) out.flag(`${at}.id`, 'duplicate')
    seen.add(id)
    if (!simple && !names.has(item.stratum.trim())) out.flag(`${at}.stratum`, 'stratum')
    return readItem(item, at, simple, depth, out)
  })
}

function simpleStrata(rows: SubsampleRows, units: readonly UnitInput[], unitBook: number, key: string, out: IssueSink): StratumInput[] {
  const exhaustive = units.filter((unit) => unit.exhaustive).reduce((sum, unit) => sum + unit.book_value, 0)
  const sampled = unitBook - exhaustive
  if (sampled <= 0) out.flag(`${key}.items`, 'range')
  const size = rows.estimator === 'mean_per_unit' ? out.take(`${key}.populationSize`, rows.populationSize, { required: true, positive: true, integer: true }) : undefined
  const strata: StratumInput[] = [{ name: SAMPLED_PART, book_value: sampled, ...(size === undefined ? {} : { population_size: size }) }]
  if (exhaustive > 0) strata.unshift({ name: EXHAUSTIVE_PART, book_value: exhaustive })
  return strata
}

function ownStrata(rows: SubsampleRows, unitBook: number, key: string, out: IssueSink): StratumInput[] {
  const seen = new Set<string>()
  const strata = rows.strata.map((row, index) => {
    const at = `${key}.strata.${index}`
    const name = row.name.trim()
    if (!name) out.flag(`${at}.name`, 'required')
    else if (seen.has(name)) out.flag(`${at}.name`, 'duplicate')
    seen.add(name)
    const book = out.take(`${at}.bookValue`, row.bookValue, { required: true, positive: true })
    const needsSize = rows.estimator === 'mean_per_unit' || row.populationSize.trim() !== ''
    const size = needsSize ? out.take(`${at}.populationSize`, row.populationSize, { required: true, positive: true, integer: true }) : undefined
    return { name, book_value: book, ...(size === undefined ? {} : { population_size: size }) }
  })
  const total = strata.reduce((sum, stratum) => sum + stratum.book_value, 0)
  if (Math.abs(total - unitBook) > 0.005) out.flag(`${key}.strata`, 'range')
  return strata
}

/** Teilstichprobe für die Anfrage (`depth` 1 = Teilstichprobe der Einheit). */
export function readSubsample(rows: SubsampleRows, unitBook: number, key: string, out: IssueSink, depth = 1): SubsampleInput {
  const units = readItems(rows, key, depth, out)
  if (!units.some((unit) => !unit.exhaustive)) out.flag(`${key}.items`, 'required')
  const strata = rows.strata.length ? ownStrata(rows, unitBook, key, out) : simpleStrata(rows, units, unitBook, key, out)
  return { estimator: rows.estimator, strata, units }
}
