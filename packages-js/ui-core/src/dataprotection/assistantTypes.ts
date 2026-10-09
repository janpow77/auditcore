// Vertrag des Arbeitsbereichs (Wizard, Checkliste, Status, Sperren) von
// `auditcore_dataprotection.web`: GET /activities/{id}/workspace und die
// zugehörigen Schreibaufrufe. Alle Werte berechnet der Server.

export type AssistantMode = 'gefuehrt' | 'frei'
export type QuestionKind = 'ja_nein_unklar' | 'text' | 'auswahl' | 'umsetzung'
export type StepStatus = 'vollstaendig' | 'klaerung' | 'offen'
export type TaskKind = 'unklar' | 'unbestaetigt' | 'fehlt'

export interface AssistantAnswer {
  value: string
  justification: string
  by: string
  at: string
  origin: string
}

export interface AssistantQuestion {
  id: string
  text: string
  kind: QuestionKind
  target: string
  help: string
  required: boolean
  na_allowed: boolean
  choices: { key: string; title: string }[]
  justify_values: string[]
  reference: string
  value: string | null
  answer: AssistantAnswer | null
}

export interface AssistantStep {
  id: string
  title: string
  goal: string
  status: StepStatus
  questions: AssistantQuestion[]
}

export interface AssistantTask {
  step: string
  question: string
  kind: TaskKind
}

export interface AssistantState {
  catalog_version: string
  mode: AssistantMode
  current_step: string
  previous_step: string | null
  next_step: string | null
  steps: AssistantStep[]
  tasks: AssistantTask[]
  hidden_answers: string[]
}

export interface StatusAxes {
  dokumentation: string
  dsfa_erforderlichkeit: string
  dsfa_bearbeitung: string
  konsultation: string
  zentrale_uebernahme: string
  betriebsentscheidung: string
}

export interface GateView {
  id: string
  reason: string
  role: string
  next_step: string
}

export type ChecklistStatus =
  | 'offen'
  | 'in_bearbeitung'
  | 'zur_pruefung'
  | 'nachgewiesen'
  | 'klaerungsbedarf'
  | 'nicht_erfuellt'
  | 'nicht_anwendbar'
  | 'erneut_zu_pruefen'

export interface ChecklistItemView {
  id: string
  bereich: string
  titel: string
  zustaendig: string
  sperrt: string
  nachweisarten: string[]
  status: ChecklistStatus
  evidence_ids: string[]
  owner: string
  due: string
  justification: string
  objection: string
  updated_by: string
  updated_at: string
  confirmed_by: string
}

export interface WorkspaceOverview {
  taetigkeit_id: string
  register: { register_id: string; version: number; status: string; revision: number }
  profil: { id: string; version: string; fingerprint: string }
  assistent: AssistantState
  dubletten: string[]
  status: StatusAxes
  sperren: GateView[]
  pruefpunkte: ChecklistItemView[]
  verzeichnisbefunde: string[]
  offene_aufgaben: string[]
  hinweise: string[]
  nicht_nachgewiesene_massnahmen: string[]
  folgenabschaetzung: { assessment_id: string; version: number; revision: number; status: string } | null
}

export interface ChecklistChange {
  status: ChecklistStatus
  justification?: string
  evidence_ids?: string[]
  owner?: string
  due?: string
  objection?: string
}

/** Datenzugang des Arbeitsbereichs; Rechte und Sperren prüft der Server. */
export interface AssistantPort {
  workspace: (activityId: string) => Promise<WorkspaceOverview>
  answer: (
    activityId: string,
    questionId: string,
    value: string,
    justification: string,
    expectedRevision: number | null,
  ) => Promise<WorkspaceOverview>
  confirm: (activityId: string, questionId: string, expectedRevision: number | null) => Promise<WorkspaceOverview>
  navigate: (activityId: string, mode: AssistantMode, step: string, expectedRevision: number | null) => Promise<WorkspaceOverview>
  checklist: (activityId: string, itemId: string, change: ChecklistChange, expectedRevision: number | null) => Promise<WorkspaceOverview>
}
