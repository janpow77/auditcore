import type { Comparison, ComparisonResult, Locale, SortState, SynopsisLayout, SynopsisPort, TableColumn, TableRow } from '@flowaudit/ui'
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

export interface FlowauditSynopsisProps {
  comparison?: Comparison | null
  result?: ComparisonResult | null
  comparisonId?: string
  port?: SynopsisPort | null
  title?: string
  oldLabel?: string
  newLabel?: string
  editable?: boolean
  layout?: SynopsisLayout
  locale?: Locale
}

/** `<flowaudit-synopsis>` als React-Komponente (Synopse / Versionsvergleich). */
export const FlowauditSynopsis = createElementComponent<
  FlowauditSynopsisProps,
  { onRowUpdate: string; onExport: string; onNavigate: string; onLayoutChange: string }
>('flowaudit-synopsis', {
  properties: ['comparison', 'result', 'comparisonId', 'port', 'title', 'oldLabel', 'newLabel', 'editable', 'layout', 'locale'],
  events: { onRowUpdate: 'row-update', onExport: 'export', onNavigate: 'navigate', onLayoutChange: 'update:layout' },
})
