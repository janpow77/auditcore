// Typen des REST-Vertrags auditcore_registry_sources.screening_review/1
// (Server: auditcore_registry_sources/web/_types.py, Doku: docs/ui/screening-rest.md).

export const CONTRACT = 'auditcore_registry_sources.screening_review/1'

export type ScreeningKind = 'sanctions' | 'pep'
export type Outcome = 'confirmed' | 'dismissed' | 'deferred'
export type ReviewStatus = 'open' | 'pending_second_review' | Outcome
export type SubjectStatus = 'HITS' | 'NO_HITS' | 'INCOMPLETE' | 'NOT_SEARCHED'
export type FreshnessStatus = 'current' | 'stale' | 'unknown' | 'not_judged'

export interface ActorView {
  id: string
  display_name: string
}

export interface SubjectInput {
  subject_id: string
  name: string
  birth_date: string | null
  country: string | null
  schema: string | null
  reference: string | null
}

export interface EntryView {
  entry_id: string
  schema: string
  name: string
  aliases: string[]
  aliases_total: number
  birth_date: string
  countries: string
  addresses: string
  identifiers: string
  sanctions: string
  program_ids: string
  first_seen: string
  last_seen: string
  dataset: string
}

export interface BreakdownStep {
  step: 'normalization' | 'base' | 'adjustment' | 'clamp' | 'result'
  label: string
  value?: string
  detail?: string
  points?: number
  kind?: string
}

export interface ScoreClass {
  class: string
  label: string
  from: number
}

export interface Breakdown {
  method: string
  scale: { min: number; max: number }
  steps: BreakdownStep[]
  min_score: number
  classes: ScoreClass[]
  class: string
  class_label: string
  consistent: boolean
}

export interface DecisionView {
  outcome: Outcome
  reason: string
  four_eyes: boolean
  four_eyes_source: 'policy' | 'requested' | null
  actor: ActorView
  at: string
  sequence: number
}

export interface SecondReviewView {
  approve: boolean
  reason: string
  actor: ActorView
  at: string
  sequence: number
}

export interface ReviewView {
  status: ReviewStatus
  status_label: string
  sequence: number
  decision: DecisionView | null
  second_review: SecondReviewView | null
  events: number
}

export interface HitView {
  hit_id: string
  subject_id: string
  list_key: string
  list_name: string
  source_key: string | null
  entry: EntryView
  matched_name: string
  matched_field: 'name' | 'alias'
  raw_score: number
  score: number
  confidence: string
  dob_conflict: boolean
  country_conflict: boolean
  below_min_score: boolean
  indicators: string[]
  breakdown: Breakdown
  review: ReviewView
}

export interface FindingView {
  list_key: string
  list_name: string
  source_key: string | null
  searched: boolean
  entry_count: number
  as_of: string | null
  retrieved_at: string | null
  hit_count: number
  note: string | null
}

export interface SubjectView {
  subject_id: string
  input: SubjectInput
  status: SubjectStatus
  normalized_query: string
  min_score: number
  findings: FindingView[]
  hits: HitView[]
  hits_before_filter: number
  total_hits: number
  truncated: boolean
  notice: string
  limitations: string[]
}

export interface FreshnessView {
  status: FreshnessStatus
  label: string
  age_days: number | null
  stale_after_days: number | null
}

export interface ListInfo {
  key: string
  source_key: string | null
  name: string
  issuer: string
  url: string
  format: string
  provider: string
  licence_claimed_in_source: string | null
  data_licence: { status?: string; note?: string }
}

export interface SourceView {
  list: ListInfo
  kind: ScreeningKind
  entry_count: number
  as_of: string | null
  retrieved_at: string | null
  content_sha256: string | null
  note: string | null
  searchable: boolean
  freshness: FreshnessView
}

export interface ProfileView {
  id: string
  version: string
  fingerprint: string
  status: string
  kind: ScreeningKind
  legal_status: string
  default_min_score: number
  scale: { min: number; max: number }
  recommended: boolean
}

export interface SettingsView {
  contract: string
  profiles: ProfileView[]
  four_eyes_outcomes: Outcome[]
  stale_after_days: number | null
}

export interface SourcesView {
  contract: string
  checked_at: string
  sources: SourceView[]
}

export interface RunSummary {
  run_id: string
  created_at: string
  created_by: ActorView
  kind: ScreeningKind
  case_reference: string | null
  profile: { id: string; version: string; fingerprint: string; status: string }
  subject_count: number
  subjects_with_hits: number
  subjects_incomplete: number
  hit_count: number
  review_counts: Record<ReviewStatus, number>
  review_complete: boolean
  last_sequence: number
}

export interface RunRequestRecord {
  kind: ScreeningKind
  profile: RunSummary['profile']
  lists: string[]
  min_score: number | null
  limit: number
  case_reference: string | null
  subjects: SubjectInput[]
}

export interface RunView extends RunSummary {
  contract: string
  request: RunRequestRecord
  sources: SourceView[]
  subjects: SubjectView[]
}

export interface LogEntry {
  run_id: string
  sequence: number
  type: 'run_created' | 'decision_recorded' | 'second_review_recorded'
  type_label: string
  at: string
  actor: ActorView
  hit_id: string | null
  hit?: { subject_name: string; entry_name: string; list_name: string } | null
  data: Record<string, unknown>
  outcome_label?: string
}

export interface LogView {
  contract: string
  run_id: string
  events: LogEntry[]
}

export interface SubjectRequest {
  name: string
  birth_date?: string
  country?: string
  schema?: string
  reference?: string
}

export interface RunRequest {
  kind: ScreeningKind
  profile: { id: string; version: string }
  subjects: SubjectRequest[]
  lists?: string[]
  min_score?: number
  limit?: number
  case_reference?: string
}

export interface DecisionRequest {
  outcome: Outcome
  reason: string
  four_eyes: boolean
  expected_sequence?: number
}

export interface SecondReviewRequest {
  approve: boolean
  reason: string
  expected_sequence?: number
}

export interface ApiErrorBody {
  error: { code: string; message: string; details: Record<string, unknown> }
}

export type RunQuery = Partial<Record<'status' | 'list' | 'subject' | 'confidence' | 'min_score', string>>

/**
 * Port der Screening-Trefferprüfung. Die Komponente ruft nie selbst `fetch`
 * auf; `createScreeningRestPort` ist die mitgelieferte REST-Umsetzung.
 */
export interface ScreeningPort {
  settings: () => Promise<SettingsView>
  sources: () => Promise<SourcesView>
  runs: () => Promise<{ contract: string; runs: RunSummary[] }>
  createRun: (request: RunRequest) => Promise<RunView>
  run: (runId: string, query?: RunQuery) => Promise<RunView>
  log: (runId: string) => Promise<LogView>
  decide: (runId: string, hitId: string, decision: DecisionRequest) => Promise<HitView>
  secondReview: (runId: string, hitId: string, review: SecondReviewRequest) => Promise<HitView>
}
