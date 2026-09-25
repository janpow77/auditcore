import type { SortState, TableColumn, TableRow, Locale } from '@flowaudit/ui'
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
