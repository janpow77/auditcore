// Vertrag `dataprotection_ui/1` von `auditcore_dataprotection.web` (docs/ui/dataprotection-rest.md).
// Feldnamen wie im JSON des Servers; Inhalte des Verzeichnisses mit den Feldnamen der Bibliothek.

export const CONTRACT = 'dataprotection_ui/1'

export type FieldKind = 'text' | 'flag' | 'count'
export type FieldValue = string | boolean | number | null

export interface RegisterColumn {
  key: string
  title: string
  reference: string
  kind: FieldKind
  required: boolean
}

export interface QuestionView {
  key: string
  text: string
  reference: string
  /** `hart` = Muss-Kriterium, `punkt` = Kriterium WP 248, `fria` = Hochrisiko-KI. */
  effect: string
  explanation: string
}

export interface BlockView {
  key: string
  title: string
  questions: QuestionView[]
}

export interface LevelView {
  value: number
  label: string
}

export interface MeasureView {
  key: string
  title: string
  category: string
  reduces_severity: number
  reduces_likelihood: number
}

export interface KeyTitle {
  key: string
  title: string
}

export interface DossierFieldView extends KeyTitle {
  kind: 'text' | 'date' | 'choice'
  required: boolean
  choices: KeyTitle[]
}

export interface DataProtectionProfile {
  contract: string
  profile: { id: string; version: string; fingerprint: string; regime: string; regime_title: string; release_mode: string }
  register: { columns: RegisterColumn[] }
  screening: { blocks: BlockView[]; points_threshold: number }
  risk: {
    scale_min: number
    scale_max: number
    severity_levels: LevelView[]
    likelihood_levels: LevelView[]
    dimensions: KeyTitle[]
    measures: MeasureView[]
    bands: string[]
    method: string
  }
  decisions: KeyTitle[]
  dossier_fields: DossierFieldView[]
}

/** Hinweis der Vollständigkeitsprüfung; `subject` = `<Tätigkeits-ID>:<Feld>` oder `deckblatt:<Teil>`. */
export interface Issue {
  code: string
  message: string
  blocking: boolean
  subject: string
}

export type Activity = Record<string, FieldValue> & { id?: string }

export interface Person {
  name?: string
  [field: string]: string | undefined
}

export interface RegisterContent {
  deckblatt: { verantwortlicher?: Person; dsb?: Person; [part: string]: Person | undefined }
  referate: string[]
  taetigkeiten: Activity[]
}

export type RegisterStatus = 'entwurf' | 'freigegeben' | 'abgeloest'

export interface VersionSummary {
  version: number
  status: RegisterStatus
  created_by: string
  created_at: string
  released_by: string | null
  released_at: string | null
  activities: number
}

export interface VersionView extends VersionSummary {
  revision: number
  locked: boolean
  content: RegisterContent
  content_hash: string
  editors: string[]
  predecessor_version: number | null
  issues: Issue[]
}

export interface RegisterState {
  contract: string
  draft: VersionView | null
  released: VersionView | null
  versions: VersionSummary[]
}

export interface OverviewRow {
  id: string
  position: number
  name: string
  referat: string
  zweck: string
  vvt_version: number
  vvt_status: RegisterStatus
  dsfa: null | {
    id: string
    version: number
    status: AssessmentStatus
    entscheidung: string | null
    freigegeben_am: string | null
    pruefung_erforderlich: boolean
  }
}

export type AnswerValue = 'ja' | 'nein' | 'unbekannt'
export type AssessmentStatus = 'entwurf' | 'dsb_beteiligung' | 'freigegeben' | 'abgeloest'

export interface AnswerInput {
  value: AnswerValue
  justification: string
}

export interface ScenarioInput {
  dimension: string
  description: string
  severity: number
  likelihood: number
  measures: string[]
  residual_severity: number | null
  residual_likelihood: number | null
  residual_justification: string
}

export interface ScenarioResult {
  index: number
  dimension_title: string
  description: string
  gross: number
  gross_band: string
  net: number
  net_band: string
  net_severity: number
  net_likelihood: number
  measure_titles: string[]
  explicit_residual: string[]
}

export interface Proposal {
  profile: { id: string; version: string; fingerprint: string }
  recommendation: string
  recommendation_text: string
  reasoning: string
  consultation_required: boolean
  consultation_notice?: { status: string; text: string; final: boolean }
  issues: Issue[]
  screening: {
    outcome: 'pflicht' | 'keine_pflicht' | 'unvollstaendig'
    points: number
    points_threshold: number
    hard_triggers: string[]
    point_criteria: string[]
    fria_required: boolean | null
    unanswered: string[]
    unknown: string[]
    complete: boolean
    reasoning: string
  }
  risk: null | {
    gross_maximum: number
    net_maximum: number
    net_band: string
    gross_band?: string
    scenarios: ScenarioResult[]
  }
}

export interface AssessmentSummary {
  id: string
  version: number
  status: AssessmentStatus
  decision: string | null
  created_at: string
  released_by: string | null
  released_at: string | null
}

export interface AssessmentView extends AssessmentSummary {
  contract: string
  activity_id: string
  activity_name: string
  revision: number
  locked: boolean
  register_version: number
  profile: { id: string; version: string }
  answers: Record<string, AnswerInput>
  scenarios: ScenarioInput[]
  necessity: string
  proportionality: string
  dossier: Record<string, string>
  proposal: Proposal
  created_by: string
  updated_at: string
  editors: string[]
  deviation: boolean
  deviation_justification: string | null
  conditions: string[]
  decided_by: string | null
  decided_at: string | null
  dpo_requested_from: string | null
  dpo_requested_on: string | null
  release_open_points: string[]
  open_points: string[]
  release_blockers: string[]
  versions: AssessmentSummary[]
}

/** Erhebung einer Folgenabschätzung, wie sie `POST /assessments/{id}` erwartet. */
export interface SurveyInput {
  answers: Record<string, AnswerInput>
  scenarios: ScenarioInput[]
  necessity: string
  proportionality: string
  /** Nur Profile nach Schema 2 (EDSA-Vorlage); sonst weglassen. */
  dossier?: Record<string, string>
}

export interface DecisionInput {
  decision: string
  justification: string
  conditions: string[]
}

export type RegisterExportFormat = 'html' | 'markdown' | 'csv'
export type AssessmentExportFormat = 'html' | 'markdown'

export interface ExportedFile {
  blob: Blob
  filename: string
  mediaType: string
}

/**
 * Datenzugang der Komponenten. Die mitgelieferte Umsetzung ist
 * `createDataProtectionRestPort`; Anwendungen können eigene Ports übergeben.
 */
export interface DataProtectionPort {
  profile: () => Promise<DataProtectionProfile>
  register: () => Promise<RegisterState>
  checkRegister: (content: RegisterContent) => Promise<{ issues: Issue[] }>
  saveDraft: (content: RegisterContent, expectedRevision: number | null) => Promise<VersionView>
  releaseRegister: (expectedRevision: number) => Promise<VersionView>
  exportRegister: (format: RegisterExportFormat, source: 'draft' | 'released') => Promise<ExportedFile>
  overview: () => Promise<{ items: OverviewRow[] }>
  startAssessment: (activityId: string) => Promise<AssessmentView>
  assessment: (id: string) => Promise<AssessmentView>
  calculate: (answers: Record<string, AnswerInput>, scenarios: ScenarioInput[]) => Promise<Proposal>
  updateAssessment: (id: string, expectedRevision: number, survey: SurveyInput) => Promise<AssessmentView>
  decide: (id: string, expectedRevision: number, decision: DecisionInput) => Promise<AssessmentView>
  requestDpo: (id: string, expectedRevision: number, requestedFrom: string, requestedOn: string) => Promise<AssessmentView>
  releaseAssessment: (id: string, expectedRevision: number) => Promise<AssessmentView>
  reassess: (id: string) => Promise<AssessmentView>
  exportAssessment: (id: string, format: AssessmentExportFormat) => Promise<ExportedFile>
}
