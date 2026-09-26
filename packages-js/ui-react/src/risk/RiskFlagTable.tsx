import type { TableColumn, TableRow } from '@auditcore/common'
import { riskMessages, type FlagState, type Locale } from '@auditcore/ui-core'
import { useTranslation } from '../i18n'
import { FlowauditTable } from '../table/FlowauditTable'
import { RiskFlagState } from './RiskFlagState'

export interface RiskFlagTableProps {
  columns?: readonly TableColumn[]
  rows?: readonly TableRow[]
  /** Codes der Regelspalten (Zellen zeigen den Zustand). */
  codes?: readonly string[]
  selected?: number | null
  locale?: Locale
  onRecordSelect?: (index: number) => void
}

const STATES: readonly string[] = ['hit', 'clear', 'undetermined', 'skipped']

function cellState(value: unknown): FlagState {
  return typeof value === 'string' && STATES.includes(value) ? (value as FlagState) : 'absent'
}

/** Merkmale je Datensatz; Zeilen per Maus und Enter wählbar, wie `RiskFlagTable`. */
export function RiskFlagTable({ columns = [], rows = [], codes = [], selected = null, locale, onRecordSelect }: RiskFlagTableProps) {
  const { t } = useTranslation(riskMessages, locale)
  const renderCell = (column: TableColumn, row: TableRow, value: unknown) => {
    if (column.key === 'record') {
      return <span className="fa-risk-table__record" aria-current={row.id === selected ? 'true' : undefined}>{String(row.record)}</span>
    }
    return codes.includes(column.key) ? <RiskFlagState state={cellState(value)} code={column.key} compact locale={locale} /> : undefined
  }
  const onRow = (row: TableRow): void => {
    if (typeof row.id === 'number') onRecordSelect?.(row.id)
  }
  return (
    <div className="fa-risk-table" data-selected={selected ?? undefined}>
      <FlowauditTable
        columns={columns}
        rows={rows}
        rowKey="id"
        caption={t('tableCaption')}
        emptyText={t('noRecords')}
        clickable
        locale={locale}
        onRowClick={onRow}
        renderCell={renderCell}
      />
    </div>
  )
}
