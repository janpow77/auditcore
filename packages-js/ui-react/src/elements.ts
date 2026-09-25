import type { BenfordPort, Evaluation, Locale, PopulationItem, ProfileDetail, RiskPort, SamplingPort, SortState, TableColumn, TableRow } from '@flowaudit/ui'
import { createElementComponent } from './createElementComponent'

export interface FlowauditTableProps {
  columns: readonly TableColumn[]
  rows: readonly TableRow[]
  rowKey?: string
  caption?: string
  emptyText?: string
  clickable?: boolean
  sort?: SortState | null
  locale?: Locale
}

/** `<flowaudit-table>` als React-Komponente. */
export const FlowauditTable = createElementComponent<FlowauditTableProps, { onRowClick: string; onSortChange: string }>(
  'flowaudit-table',
  {
    properties: ['columns', 'rows', 'rowKey', 'caption', 'emptyText', 'clickable', 'sort', 'locale'],
    events: { onRowClick: 'row-click', onSortChange: 'sort-change' },
  },
)

export interface FlowauditSamplingProps {
  port: SamplingPort | null
  items?: readonly PopulationItem[]
  locale?: Locale
}

/** `<flowaudit-sampling>` als React-Komponente: Stichprobenumfang, Auswahl mit Seed, Export. */
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

/** `<flowaudit-benford>` als React-Komponente: Verteilung, MAD, Chi², z je Ziffer. */
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

/** `<flowaudit-risk-flags>` als React-Komponente; `onRecordSelect` erhält den Index oder `null`. */
export const FlowauditRiskFlags = createElementComponent<FlowauditRiskFlagsProps, { onRecordSelect: string; onFilterChange: string }>(
  'flowaudit-risk-flags',
  {
    properties: ['evaluation', 'profile', 'port', 'heading', 'locale'],
    events: { onRecordSelect: 'record-select', onFilterChange: 'filter-change' },
  },
)
