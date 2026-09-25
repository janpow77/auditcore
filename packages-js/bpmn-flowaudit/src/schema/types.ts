/**
 * TypeScript form of the FlowAudit extensions. Empty values are absent;
 * booleans are `boolean`. Vocabulary codes (e.g. `vb`, `praeventiv`) are the
 * XML values of schema 1.1 and stay German.
 */

export interface LegalBasis {
  text?: string
  id?: string
  /** Legal act, e.g. `VO (EU) 2021/1060`. */
  act?: string
  /** Article number only, e.g. `74` (not „Art. 74“). */
  article?: string
  /** Section (§) number only. */
  section?: string
  annex?: string
  paragraph?: string
  subparagraph?: string
  sentence?: string
  point?: string
  number?: string
  version?: string
  eli?: string
  celex?: string
  url?: string
  shortTitle?: string
  note?: string
  confidential?: boolean
}

export interface Marker {
  type: string
  text?: string
  confidential?: boolean
}

/** Reference to key requirement (KA) and assessment criterion (BK). */
export interface AuditReference {
  keyRequirement?: string
  assessmentCriterion?: string
  auditType?: string
  note?: string
  confidential?: boolean
}

export interface Actor {
  role?: string
  displayName?: string
}

export interface EsiRequirement {
  code: string
  criteria?: string[]
}

export interface EsiRequirements {
  profile?: string
  requirements?: EsiRequirement[]
}

export interface Control {
  id?: string
  label?: string
  keyControl?: boolean
  controlType?: string
  execution?: string
  frequency?: string
  evidence?: string
  responsible?: string
  description?: string
  confidential?: boolean
}

export interface Risk {
  id?: string
  label?: string
  category?: string
  inherent?: string
  controlRisk?: string
  residual?: string
  controls?: string[]
  description?: string
  confidential?: boolean
}

/** Audit trail evidence at data objects and data stores. */
export interface Evidence {
  documentType?: string
  storageLocation?: string
  itSystem?: string
  retentionPeriod?: string
  note?: string
  confidential?: boolean
}

/** Walk-through or control test step. */
export interface AuditStep {
  id?: string
  case?: string
  document?: string
  result?: string
  date?: string
  tester?: string
  control?: string
  sampleSize?: string
  population?: string
  remark?: string
  confidential?: boolean
}

export interface AuditFinding {
  id?: string
  /** Stable finding reference, e.g. `T15 F1`. */
  reference?: string
  findingType?: string
  severity?: string
  keyRequirement?: string
  assessmentCriterion?: string
  deadline?: string
  status?: string
  description?: string
  recommendation?: string
  confidential?: boolean
}

export interface Source {
  sourceType?: string
  location?: string
  date?: string
  reference?: string
  text?: string
  confidential?: boolean
}

/** Stable domain key towards checklists and notes (`prueffeld`, `feststellung_ref`, `register`). */
export interface CrossReference {
  kind?: string
  key?: string
  document?: string
  confidential?: boolean
}

export interface Deadline {
  value?: string
  unit?: string
  basis?: string
  note?: string
  legalBases?: LegalBasis[]
}

export type DiagramStatus = 'entwurf' | 'in_pruefung' | 'freigegeben' | 'archiviert'

export interface DiagramInfo {
  schemaVersion?: string
  profile?: string
  title?: string
  subtitle?: string
  processOwner?: string
  processType?: string
  version?: string
  status?: DiagramStatus | string
  validFrom?: string
  validUntil?: string
  author?: string
  approvedBy?: string
  approvedOn?: string
  headerColor?: string
  headerTextColor?: string
  programmingPeriod?: string
  programme?: string
  cci?: string
  confidentiality?: string
  variant?: string
  referenceDiagram?: string
  systemCutoffDate?: string
  description?: string
  keywords?: string[]
  funds?: string[]
  legalBases?: LegalBasis[]
  auditReferences?: AuditReference[]
  risks?: Risk[]
  findings?: AuditFinding[]
  sources?: Source[]
  crossReferences?: CrossReference[]
}

/** All FlowAudit data at one BPMN element (`Erweiterungen` in auditcore_bpmn). */
export interface Extensions {
  legalBases: LegalBasis[]
  internalNote?: string
  markers: Marker[]
  auditReferences: AuditReference[]
  actor?: Actor
  controls: Control[]
  risks: Risk[]
  evidence: Evidence[]
  auditSteps: AuditStep[]
  findings: AuditFinding[]
  sources: Source[]
  deadlines: Deadline[]
  crossReferences: CrossReference[]
  esi?: EsiRequirements
  diagramInfo?: DiagramInfo
}

export type ListExtensionKey =
  | 'legalBases'
  | 'markers'
  | 'auditReferences'
  | 'controls'
  | 'risks'
  | 'evidence'
  | 'auditSteps'
  | 'findings'
  | 'sources'
  | 'deadlines'
  | 'crossReferences'

export function emptyExtensions(): Extensions {
  return {
    legalBases: [],
    markers: [],
    auditReferences: [],
    controls: [],
    risks: [],
    evidence: [],
    auditSteps: [],
    findings: [],
    sources: [],
    deadlines: [],
    crossReferences: [],
  }
}
