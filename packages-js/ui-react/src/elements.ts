import type { BenfordPort, Locale, PopulationItem, SamplingPort, ScreeningError, ScreeningPort, SortState, TableColumn, TableRow } from '@flowaudit/ui'
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

export interface FlowauditScreeningReviewProps {
  port: ScreeningPort | null
  runId?: string
  locale?: Locale
}

/** `<flowaudit-screening-review>` als React-Komponente: Sanktionslisten-/PEP-Treffer prüfen und entscheiden. */
export const FlowauditScreeningReview = createElementComponent<
  FlowauditScreeningReviewProps,
  { onRunCreated: string; onDecided: string; onError: string }
>('flowaudit-screening-review', {
  properties: ['port', 'runId', 'locale'],
  events: { onRunCreated: 'run-created', onDecided: 'decided', onError: 'error' },
})

/** Nutzdaten des Ereignisses `error` der Screening-Trefferprüfung. */
export type FlowauditScreeningError = ScreeningError
