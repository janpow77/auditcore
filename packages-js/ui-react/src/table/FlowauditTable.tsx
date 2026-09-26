import { useMemo, useState, type ReactNode } from 'react'
import { ariaSort, nextSort, sortRows, type SortState, type TableColumn, type TableRow } from '@flowaudit/common'
import { baseMessages, cellAlignClass, cellText, rowKeyOf, sortIcon, type Locale, type Translate } from '@flowaudit/ui-core'
import { Icon } from '../base/Icon'
import { useTranslation } from '../i18n'
import { classes } from '../store'

type BaseKey = keyof typeof baseMessages.de

export interface FlowauditTableProps {
  columns?: readonly TableColumn[]
  rows?: readonly TableRow[]
  rowKey?: string
  caption?: string
  emptyText?: string
  /** Zeilen sind anklickbar (Maus und Enter) und lösen `onRowClick` aus. */
  clickable?: boolean
  locale?: Locale
  /** Gesteuerte Sortierung; ohne Angabe verwaltet die Tabelle sie selbst (Start: `defaultSort`). */
  sort?: SortState | null
  defaultSort?: SortState | null
  onSortChange?: (sort: SortState | null) => void
  onRowClick?: (row: TableRow) => void
  /** Eigene Zelle (Gegenstück zum Vue-Slot `cell-<key>`); `undefined` = Standardtext. */
  renderCell?: (column: TableColumn, row: TableRow, value: unknown) => ReactNode
  /** `data-testid` am Rahmen (in Vue als durchgereichtes Attribut). */
  testId?: string
}

function HeaderCell({ column, sort, t, onToggle }: { column: TableColumn; sort: SortState | null; t: Translate<BaseKey>; onToggle: (column: TableColumn) => void }) {
  return (
    <th scope="col" className={cellAlignClass(column)} aria-sort={column.sortable ? ariaSort(sort, column.key) : undefined}>
      {column.sortable ? (
        <button type="button" className="fa-table__sort" aria-label={t('sortBy', { column: column.label })} onClick={() => onToggle(column)}>
          <span>{column.label}</span>
          <Icon name={sortIcon(sort, column.key)} size={14} />
        </button>
      ) : (
        <span>{column.label}</span>
      )}
    </th>
  )
}

function useTableSort(props: FlowauditTableProps): [SortState | null, (column: TableColumn) => void] {
  const [own, setOwn] = useState<SortState | null>(props.defaultSort ?? null)
  const sort = props.sort === undefined ? own : props.sort
  function toggle(column: TableColumn): void {
    if (!column.sortable) return
    const next = nextSort(sort, column.key)
    setOwn(next)
    props.onSortChange?.(next)
  }
  return [sort, toggle]
}

/** Tabelle wie `FaTable`: Sortierung per Schaltfläche (aria-sort), anklickbare Zeilen per Maus und Enter. */
export function FlowauditTable(props: FlowauditTableProps) {
  const { columns = [], rows = [], rowKey = 'id', clickable = false } = props
  const { t, locale } = useTranslation(baseMessages, props.locale)
  const [sort, toggle] = useTableSort(props)
  const sorted = useMemo(() => sortRows(rows, sort, locale), [rows, sort, locale])
  const click = (row: TableRow): void => {
    if (clickable) props.onRowClick?.(row)
  }
  return (
    <div className="fa-table-wrap" data-testid={props.testId}>
      <table className={classes('fa-table', clickable && 'fa-table--clickable')}>
        {props.caption ? <caption className="fa-table__caption">{props.caption}</caption> : null}
        <thead>
          <tr>
            {columns.map((column) => <HeaderCell key={column.key} column={column} sort={sort} t={t} onToggle={toggle} />)}
          </tr>
        </thead>
        <tbody>
          {sorted.length === 0 ? (
            <tr>
              <td className="fa-table__empty" colSpan={columns.length}>{props.emptyText || t('tableEmpty')}</td>
            </tr>
          ) : null}
          {sorted.map((row, index) => (
            <tr key={rowKeyOf(row, rowKey, index)} tabIndex={clickable ? 0 : undefined} onClick={() => click(row)} onKeyDown={(event) => event.key === 'Enter' && click(row)}>
              {columns.map((column) => (
                <td key={column.key} className={cellAlignClass(column)}>{props.renderCell?.(column, row, row[column.key]) ?? cellText(column, row)}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
