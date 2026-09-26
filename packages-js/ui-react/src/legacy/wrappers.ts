import type { BenfordPort, Evaluation, Locale, PopulationItem, ProfileDetail, RiskPort, SamplingPort, ScreeningError, ScreeningPort } from '@flowaudit/ui'
import { createElementComponent } from './createElementComponent'

export interface FlowauditSamplingProps {
  port: SamplingPort | null
  items?: readonly PopulationItem[]
  locale?: Locale
}

/**
 * `<flowaudit-sampling>` als React-Komponente: Stichprobenumfang, Auswahl mit Seed, Export.
 * @deprecated Hülle um eine Vue-Web-Component (braucht Vue); nur bis zur nativen React-Fassung.
 */
export const FlowauditSampling = createElementComponent<
  FlowauditSamplingProps,
  { onSizeCalculated: string; onSelectionDrawn: string; onError: string }
>('flowaudit-sampling', {
  properties: ['port', 'items', 'locale'],
  events: { onSizeCalculated: 'size-calculated', onSelectionDrawn: 'selection-drawn', onError: 'error' },
})

export interface FlowauditBenfordProps {
  port: BenfordPort | null
  values?: readonly (number | null)[]
  locale?: Locale
}

/**
 * `<flowaudit-benford>` als React-Komponente: Verteilung, MAD, Chi², z je Ziffer.
 * @deprecated Hülle um eine Vue-Web-Component (braucht Vue); nur bis zur nativen React-Fassung.
 */
export const FlowauditBenford = createElementComponent<FlowauditBenfordProps, { onAnalysisCompleted: string; onError: string }>(
  'flowaudit-benford',
  { properties: ['port', 'values', 'locale'], events: { onAnalysisCompleted: 'analysis-completed', onError: 'error' } },
)

export interface FlowauditRiskFlagsProps {
  /** Antwort von `POST /evaluate` (auditcore_risk.web, docs/ui/risk-rest.md). */
  evaluation: Evaluation | null
  /** Antwort von `GET /profiles/{id}/{version}`; optional, zeigt Regeln und Eingabefelder. */
  profile?: ProfileDetail | null
  /** Optional: lädt `profile` nach (`createRiskRestPort({ baseUrl })`). */
  port?: RiskPort | null
  heading?: string
  locale?: Locale
}

/**
 * `<flowaudit-risk-flags>` als React-Komponente; `onRecordSelect` erhält den Index oder `null`.
 * @deprecated Hülle um eine Vue-Web-Component (braucht Vue); nur bis zur nativen React-Fassung.
 */
export const FlowauditRiskFlags = createElementComponent<FlowauditRiskFlagsProps, { onRecordSelect: string; onFilterChange: string }>(
  'flowaudit-risk-flags',
  {
    properties: ['evaluation', 'profile', 'port', 'heading', 'locale'],
    events: { onRecordSelect: 'record-select', onFilterChange: 'filter-change' },
  },
)

export interface FlowauditScreeningReviewProps {
  port: ScreeningPort | null
  runId?: string
  locale?: Locale
}

/**
 * `<flowaudit-screening-review>` als React-Komponente: Sanktionslisten-/PEP-Treffer prüfen und entscheiden.
 * @deprecated Hülle um eine Vue-Web-Component (braucht Vue); nur bis zur nativen React-Fassung.
 */
export const FlowauditScreeningReview = createElementComponent<
  FlowauditScreeningReviewProps,
  { onRunCreated: string; onDecided: string; onError: string }
>('flowaudit-screening-review', {
  properties: ['port', 'runId', 'locale'],
  events: { onRunCreated: 'run-created', onDecided: 'decided', onError: 'error' },
})

/** Nutzdaten des Ereignisses `error` der Screening-Trefferprüfung. */
export type FlowauditScreeningError = ScreeningError
