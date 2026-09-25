/**
 * Framework-freie View-Logik der Risiko-Merkmale: Zustand je Datensatz und
 * Regel, Verteilung je Code, Filter und Einträge für die Detailkarten.
 */
import type { DatasetFinding, Evaluation, FlagHit, JsonObject, JsonValue, RecordView, RuleView } from '../types'

/** Zustand einer Regel für einen Datensatz. */
export type FlagState = 'hit' | 'clear' | 'undetermined' | 'skipped' | 'absent'
export const FLAG_STATES: readonly FlagState[] = ['hit', 'undetermined', 'clear', 'skipped', 'absent']

export function flagState(record: RecordView, code: string, skipped: Readonly<Record<string, string>>): FlagState {
  if (code in skipped) return 'skipped'
  const flag = record.flags[code]
  if (flag === true) return 'hit'
  if (flag === false) return 'clear'
  if (flag === null) return 'undetermined'
  return 'absent'
}

/** Regeln der Auswertung; ohne `rules` aus den Codes der Datensätze abgeleitet. */
export function evaluationRules(evaluation: Evaluation): RuleView[] {
  if (evaluation.rules && evaluation.rules.length > 0) return evaluation.rules
  const codes = new Set<string>()
  for (const record of evaluation.records) for (const code of Object.keys(record.flags)) codes.add(code)
  for (const code of Object.keys(evaluation.skipped)) codes.add(code)
  return [...codes].map((code) => ({
    code, label: code, kind: '', scope: 'record', severity: null, interpretation: 'indicator', note: null,
    requires: [], when_missing_columns: 'error', inputs: [], parameters: {}, origin: {},
  }))
}

export function recordRules(evaluation: Evaluation): RuleView[] {
  return evaluationRules(evaluation).filter((rule) => rule.scope !== 'dataset')
}

export interface RiskDistributionRow {
  code: string
  label: string
  hit: number
  clear: number
  undetermined: number
  total: number
  /** Anteil der Treffer an allen Datensätzen (0–1). */
  share: number
  skipped: string | null
  /** Begründung → Anzahl der unbestimmten Datensätze. */
  reasons: Record<string, number>
  /** Volumen laut Zusammenfassung des Profils, falls vorhanden. */
  volume: number | null
}

function summaryVolume(summary: readonly JsonObject[], code: string): number | null {
  const entry = summary.find((item) => item.code === code)
  const volume = entry?.volumen
  return typeof volume === 'number' ? volume : null
}

function countStates(evaluation: Evaluation, code: string): Pick<RiskDistributionRow, 'hit' | 'clear' | 'undetermined' | 'reasons'> {
  const counts = { hit: 0, clear: 0, undetermined: 0, reasons: {} as Record<string, number> }
  for (const record of evaluation.records) {
    const state = flagState(record, code, evaluation.skipped)
    if (state === 'hit') counts.hit += 1
    else if (state === 'clear') counts.clear += 1
    else if (state === 'undetermined') {
      counts.undetermined += 1
      const reason = record.undetermined[code] ?? ''
      counts.reasons[reason] = (counts.reasons[reason] ?? 0) + 1
    }
  }
  return counts
}

/** Verteilung je Regel in Profilreihenfolge (nur Datensatzregeln). */
export function distribution(evaluation: Evaluation): RiskDistributionRow[] {
  const total = evaluation.records.length
  return recordRules(evaluation).map((rule) => {
    const counts = countStates(evaluation, rule.code)
    return {
      code: rule.code,
      label: rule.label,
      ...counts,
      total,
      share: total > 0 ? counts.hit / total : 0,
      skipped: evaluation.skipped[rule.code] ?? null,
      volume: summaryVolume(evaluation.summary, rule.code),
    }
  })
}

export interface Totals {
  records: number
  withHits: number
  withUndetermined: number
  skippedRules: number
}

export function totals(evaluation: Evaluation): Totals {
  return {
    records: evaluation.records.length,
    withHits: evaluation.records.filter((record) => record.codes.length > 0).length,
    withUndetermined: evaluation.records.filter((record) => Object.keys(record.undetermined).length > 0).length,
    skippedRules: Object.keys(evaluation.skipped).length,
  }
}

export function triggeredDataset(evaluation: Evaluation): DatasetFinding[] {
  return evaluation.dataset.filter((finding) => finding.triggered)
}

/** Filter: `affected` = Treffer oder unbestimmt; `all` = jeder Datensatz. */
export type StateFilter = 'affected' | 'hit' | 'undetermined' | 'clear' | 'all'

export interface RiskFilter {
  code: string | null
  state: StateFilter
  query: string
}

export const DEFAULT_FILTER: RiskFilter = { code: null, state: 'affected', query: '' }

function matchesState(states: readonly FlagState[], wanted: StateFilter): boolean {
  if (wanted === 'all') return true
  if (wanted === 'affected') return states.some((state) => state === 'hit' || state === 'undetermined')
  if (wanted === 'clear') return states.every((state) => state !== 'hit' && state !== 'undetermined')
  return states.includes(wanted)
}

export function recordLabel(record: RecordView): string {
  const key = record.key
  return key === null || key === undefined || key === '' ? `#${record.index + 1}` : String(key)
}

function matchesQuery(record: RecordView, query: string): boolean {
  const needle = query.trim().toLocaleLowerCase('de')
  if (!needle) return true
  const haystack = [recordLabel(record), ...record.codes, ...record.hits.map((hit) => hit.reason)]
  return haystack.some((text) => text.toLocaleLowerCase('de').includes(needle))
}

export function filterRecords(evaluation: Evaluation, filter: RiskFilter): RecordView[] {
  const codes = filter.code ? [filter.code] : recordRules(evaluation).map((rule) => rule.code)
  return evaluation.records.filter((record) => {
    const states = codes.map((code) => flagState(record, code, evaluation.skipped))
    return matchesState(states, filter.state) && matchesQuery(record, filter.query)
  })
}

/** Ein Eintrag der Detailansicht: Treffer oder unbestimmtes Merkmal eines Datensatzes. */
export interface FlagEntry {
  code: string
  label: string
  state: 'hit' | 'undetermined'
  reason: string
  severity: string | null
  note: string | null
  inputs: JsonObject
  parameters: JsonObject
  evidence: JsonObject
  origin: JsonObject
  messages: Record<string, string> | null
}

function hitEntry(hit: FlagHit, rule: RuleView | undefined, inputs: JsonObject): FlagEntry {
  return {
    code: hit.code, label: hit.label, state: 'hit', reason: hit.reason, severity: hit.severity, note: hit.note,
    inputs: hit.inputs ?? inputs, parameters: rule?.parameters ?? {}, evidence: hit.evidence, origin: hit.origin,
    messages: hit.messages,
  }
}

function undeterminedEntry(code: string, reason: string, rule: RuleView | undefined, inputs: JsonObject): FlagEntry {
  return {
    code, label: rule?.label ?? code, state: 'undetermined', reason, severity: rule?.severity ?? null,
    note: rule?.note ?? null, inputs, parameters: rule?.parameters ?? {}, evidence: {}, origin: rule?.origin ?? {},
    messages: null,
  }
}

/** Treffer und unbestimmte Merkmale eines Datensatzes in Profilreihenfolge. */
export function recordEntries(record: RecordView, rules: readonly RuleView[]): FlagEntry[] {
  const byCode = new Map(rules.map((rule) => [rule.code, rule]))
  const order = new Map(rules.map((rule, index) => [rule.code, index]))
  const entries = [
    ...record.hits.map((hit) => hitEntry(hit, byCode.get(hit.code), record.inputs?.[hit.code] ?? {})),
    ...Object.entries(record.undetermined).map(([code, reason]) =>
      undeterminedEntry(code, reason, byCode.get(code), record.inputs?.[code] ?? {})),
  ]
  return entries.sort((a, b) => (order.get(a.code) ?? 0) - (order.get(b.code) ?? 0))
}

/** Objekt als Liste `[Schlüssel, Wert]` in Einfügereihenfolge (für deklarative Tabellen). */
export function pairs(value: JsonObject | null | undefined): Array<[string, JsonValue]> {
  return value ? Object.entries(value) : []
}
