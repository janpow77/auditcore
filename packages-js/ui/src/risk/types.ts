/**
 * Datentypen des REST-Vertrags `auditcore_risk.web` (docs/ui/risk-rest.md).
 * Die Komponenten lesen nur diese Felder; unbekannte Felder werden ignoriert.
 */

export type JsonValue = string | number | boolean | null | JsonValue[] | { [key: string]: JsonValue }
export type JsonObject = { [key: string]: JsonValue }

export type ProfileStatus = 'LEGACY_CHARACTERIZED' | 'CANDIDATE_HUMAN_DECISION_REQUIRED' | 'APPROVED'
export type WhenMissingColumns = 'error' | 'skip' | 'all_false' | 'undetermined'
export type Severity = 'INFO' | 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'

export interface ProfileReference {
  id: string
  version: string
  fingerprint: string
  status: ProfileStatus | string
}

export interface RuleView {
  code: string
  label: string
  kind: string
  scope: 'record' | 'dataset' | string
  severity: Severity | string | null
  interpretation: string
  note: string | null
  requires: string[]
  when_missing_columns: WhenMissingColumns | string
  inputs: string[]
  parameters: JsonObject
  origin: JsonObject
}

export interface FieldUse {
  code: string
  label: string
  role: string
  absent: string
  empty: string
}

export interface FieldEntry {
  name: string
  meaning: string | null
  meaning_source: string | null
  requirement: 'required' | 'value_required' | 'optional' | string
  required_by: string[]
  value_required_by: string[]
  uses: FieldUse[]
}

export interface ProfileDetail extends ProfileReference {
  kind: string
  legal_status: string
  rule_count: number
  field_count: number
  source: JsonObject
  input_contract: string | null
  open_decisions: string[]
  summary_format: string | null
  assessment: string | null
  rules: RuleView[]
  fields: FieldEntry[]
}

export interface FlagHit {
  code: string
  label: string
  reason: string
  interpretation: string
  note: string | null
  severity: Severity | string | null
  messages: Record<string, string> | null
  evidence: JsonObject
  origin: JsonObject
  inputs?: JsonObject
}

export interface RecordView {
  index: number
  key?: JsonValue
  /** Code → Treffer (`true`), kein Merkmal (`false`) oder unbestimmt (`null`). */
  flags: Record<string, boolean | null>
  codes: string[]
  undetermined: Record<string, string>
  values: JsonObject
  assessment: JsonObject | null
  hits: FlagHit[]
  /** Code → gelesene Eingabefelder mit Werten (Treffer und unbestimmte Merkmale). */
  inputs?: Record<string, JsonObject>
}

export interface DatasetFinding {
  code: string
  label: string
  triggered: boolean
  value: number | string | null
  reason: string
  evidence: JsonObject
}

export interface Evaluation {
  library: string
  profile: ProfileReference
  records: RecordView[]
  dataset: DatasetFinding[]
  /** Übersprungene Regeln: Code → Grund (z. B. „Spalten fehlen: …“). */
  skipped: Record<string, string>
  summary: JsonObject[]
  rules?: RuleView[]
  columns?: string[]
  missing_columns?: Record<string, string[]>
}
