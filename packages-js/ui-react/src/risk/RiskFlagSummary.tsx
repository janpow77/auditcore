import type { ReactNode } from 'react'
import type { TableColumn, TableRow } from '@auditcore/common'
import {
  formatAmount,
  formatShare,
  formatValue,
  riskMessages,
  type DatasetFinding,
  type Locale,
  type RiskDistributionRow,
  type RiskTranslate,
  type Totals,
} from '@auditcore/ui-core'
import { useTranslation } from '../i18n'
import { FlowauditTable } from '../table/FlowauditTable'
import { RiskFlagState } from './RiskFlagState'

export interface RiskFlagSummaryProps {
  rows?: readonly RiskDistributionRow[]
  totals?: Totals | null
  dataset?: readonly DatasetFinding[]
  missingColumns?: Readonly<Record<string, readonly string[]>>
  locale?: Locale
  onCodeSelect?: (code: string) => void
}

interface CellContext {
  t: RiskTranslate
  active: Locale
  locale?: Locale
  maxHits: number
  missingColumns: Readonly<Record<string, readonly string[]>>
  onCodeSelect?: (code: string) => void
}

function summaryColumns(rows: readonly RiskDistributionRow[], t: RiskTranslate, active: Locale): TableColumn[] {
  const hasVolume = rows.some((row) => row.volume !== null)
  return [
    { key: 'code', label: t('colCode') },
    { key: 'label', label: t('colLabel') },
    { key: 'hit', label: t('colHits'), align: 'end' },
    { key: 'share', label: t('colShare'), align: 'end' },
    { key: 'undetermined', label: t('colUndetermined'), align: 'end' },
    ...(hasVolume
      ? [{ key: 'volume', label: t('colVolume'), align: 'end' as const, format: (value: unknown) => formatAmount(typeof value === 'number' ? value : null, active) }]
      : []),
  ]
}

function LabelCell({ row, ctx }: { row: RiskDistributionRow; ctx: CellContext }) {
  const missing = ctx.missingColumns[row.code]
  let note: ReactNode = null
  if (row.skipped) note = <span className="fa-risk-summary__skipped"><RiskFlagState state="skipped" locale={ctx.locale} /> {row.skipped}</span>
  else if (missing?.length) note = <span className="fa-risk-summary__skipped">{ctx.t('missingColumns', { columns: missing.join(', ') })}</span>
  return <><span>{row.label}</span>{note}</>
}

function HitCell({ row, ctx }: { row: RiskDistributionRow; ctx: CellContext }) {
  if (row.skipped) return <span aria-label={ctx.t('stateSkipped')}>–</span>
  return (
    <span className="fa-risk-summary__count">
      <span className="fa-risk-summary__bar" aria-hidden="true"><span style={{ width: `${(row.hit / ctx.maxHits) * 100}%` }} /></span>
      {' '}{formatValue(row.hit, ctx.active, '0')}
    </span>
  )
}

function UndeterminedCell({ row, ctx }: { row: RiskDistributionRow; ctx: CellContext }) {
  if (row.skipped) return <span>–</span>
  if (!row.undetermined) return <span>0</span>
  return (
    <span className="fa-risk-summary__undetermined">
      <span className="fa-risk-summary__count"><RiskFlagState state="undetermined" compact locale={ctx.locale} /> {row.undetermined}</span>
      {Object.entries(row.reasons).map(([reason, count]) => <small key={reason}>{ctx.t('reasonCount', { reason, count })}</small>)}
    </span>
  )
}

function summaryCell(column: TableColumn, value: TableRow, ctx: CellContext): ReactNode {
  const row = value as unknown as RiskDistributionRow
  switch (column.key) {
    case 'code':
      return <button type="button" className="fa-risk-summary__code" onClick={() => ctx.onCodeSelect?.(row.code)}>{row.code}</button>
    case 'label':
      return <LabelCell row={row} ctx={ctx} />
    case 'hit':
      return <HitCell row={row} ctx={ctx} />
    case 'share':
      return row.skipped ? '–' : formatShare(row.share, ctx.active)
    case 'undetermined':
      return <UndeterminedCell row={row} ctx={ctx} />
    default:
      return undefined
  }
}

function TotalsList({ totals, t, locale }: { totals: Totals; t: RiskTranslate; locale?: Locale }) {
  return (
    <ul className="fa-risk-summary__totals">
      <li>{t('totalsRecords', { count: totals.records })}</li>
      <li><RiskFlagState state="hit" compact locale={locale} /> {t('totalsHits', { count: totals.withHits })}</li>
      <li><RiskFlagState state="undetermined" compact locale={locale} /> {t('totalsUndetermined', { count: totals.withUndetermined })}</li>
      {totals.skippedRules ? <li><RiskFlagState state="skipped" compact locale={locale} /> {t('totalsSkipped', { count: totals.skippedRules })}</li> : null}
    </ul>
  )
}

/** Verteilung je Merkmal mit Summen und Befunden über alle Datensätze, wie `RiskFlagSummary`. */
export function RiskFlagSummary({ rows = [], totals = null, dataset = [], missingColumns = {}, locale, onCodeSelect }: RiskFlagSummaryProps) {
  const { t, locale: active } = useTranslation(riskMessages, locale)
  const ctx: CellContext = { t, active, locale, maxHits: Math.max(1, ...rows.map((row) => row.hit)), missingColumns, onCodeSelect }
  const tableRows: TableRow[] = rows.map((row) => ({ ...row, id: row.code }))
  return (
    <section className="fa-risk-summary" aria-label={t('summaryTitle')}>
      {totals ? <TotalsList totals={totals} t={t} locale={locale} /> : null}
      <FlowauditTable
        columns={summaryColumns(rows, t, active)}
        rows={tableRows}
        rowKey="code"
        caption={t('summaryCaption', { count: totals?.records ?? 0 })}
        locale={locale}
        renderCell={(column, row) => summaryCell(column, row, ctx)}
      />
      {dataset.length ? (
        <div className="fa-risk-summary__dataset">
          <h3>{t('datasetTitle')}</h3>
          {dataset.map((finding) => <p key={finding.code}><strong>{finding.code}</strong> {finding.label} – {finding.reason}</p>)}
        </div>
      ) : null}
    </section>
  )
}
