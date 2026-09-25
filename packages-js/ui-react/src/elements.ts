import type { Locale, ScreeningError, ScreeningPort, SortState, TableColumn, TableRow } from '@flowaudit/ui'
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
