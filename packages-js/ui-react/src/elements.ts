import type { Evaluation, Locale, ProfileDetail, RiskPort, SortState, TableColumn, TableRow } from '@flowaudit/ui'
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
