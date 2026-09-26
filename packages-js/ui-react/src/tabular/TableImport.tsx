import { useState, type ChangeEvent } from 'react'
import type { DecimalSeparator } from '@auditcore/common'
import {
  createTableImportController,
  importDelimiterText,
  importOptionalColumn,
  importPreview,
  importRejectedLines,
  tabularMessages,
  type ImportedColumns,
  type Locale,
  type TableImportController,
  type TableImportData,
  type Translate,
  type TabularMessageKey,
} from '@auditcore/ui-core'
import { Button } from '../base/Button'
import { useTranslation } from '../i18n'
import { useElementId, useStoreState } from '../store'

export interface TableImportProps {
  /** `items`: zusätzlich Kennungs- und Schichtspalte wählbar. */
  mode?: 'values' | 'items'
  locale?: Locale
  onImport?: (columns: ImportedColumns) => void
}

type Select = ChangeEvent<HTMLSelectElement>

function ColumnSelect({ label, value, header, none, onChange }: { label: string; value: number | null; header: readonly string[]; none?: string; onChange: (value: string) => void }) {
  return (
    <label className="fa-import__field">
      <span>{label}</span>
      <select value={value ?? ''} onChange={(event: Select) => onChange(event.target.value)}>
        {none === undefined ? null : <option value="">{none}</option>}
        {header.map((name, index) => <option key={index} value={index}>{name}</option>)}
      </select>
    </label>
  )
}

function ImportFields({ state, controller, mode, t }: { state: TableImportData; controller: TableImportController; mode: 'values' | 'items'; t: Translate<TabularMessageKey> }) {
  const header = state.table?.header ?? []
  return (
    <div className="fa-import__grid">
      <label className="fa-import__check">
        <input type="checkbox" checked={state.hasHeader} onChange={(event) => { controller.setHasHeader(event.target.checked); controller.reparse() }} />
        {t('header')}
      </label>
      <ColumnSelect label={t('valueColumn')} value={state.valueColumn} header={header} onChange={(value) => controller.setValueColumn(Number(value))} />
      {mode === 'items' ? (
        <>
          <ColumnSelect label={t('idColumn')} value={state.idColumn} header={header} none={t('none')} onChange={(value) => controller.setIdColumn(importOptionalColumn(value))} />
          <ColumnSelect label={t('stratumColumn')} value={state.stratumColumn} header={header} none={t('none')} onChange={(value) => controller.setStratumColumn(importOptionalColumn(value))} />
        </>
      ) : null}
      <label className="fa-import__field">
        <span>{t('decimal')}</span>
        <select value={state.decimal} onChange={(event: Select) => controller.setDecimal(event.target.value as DecimalSeparator)}>
          <option value=",">{t('decimalComma')}</option>
          <option value=".">{t('decimalDot')}</option>
        </select>
      </label>
    </div>
  )
}

/** Datei-Import wie `TableImport` (Vue): CSV/TSV/Text lesen, Spalten zuordnen, Werte übernehmen. */
export function TableImport({ mode = 'values', locale, onImport }: TableImportProps) {
  const { t } = useTranslation(tabularMessages, locale)
  const [controller] = useState(createTableImportController)
  const state = useStoreState(controller.store)
  const id = useElementId('fa-import')
  const preview = importPreview(state)
  const onFile = async (event: ChangeEvent<HTMLInputElement>): Promise<void> => {
    const file = event.target.files?.[0]
    if (file) await controller.read(file)
  }
  return (
    <div className="fa-import">
      <label htmlFor={`${id}-file`} className="fa-import__label">{t('file')}</label>
      <input id={`${id}-file`} className="fa-import__file" type="file" accept=".csv,.tsv,.txt,text/csv,text/plain" onChange={(event) => void onFile(event)} />
      {state.table ? (
        <>
          <p className="fa-import__note" aria-live="polite">
            {t('summary', { file: state.filename, rows: state.table.rows.length, delimiter: importDelimiterText(state.table, t('tab')) })}
          </p>
          <ImportFields state={state} controller={controller} mode={mode} t={t} />
          {preview?.rejected.length ? (
            <p className="fa-import__warning" role="status">{t('rejected', { count: preview.rejected.length, lines: importRejectedLines(preview) })}</p>
          ) : null}
          <Button variant="secondary" label={t('apply')} testId="import-apply" onClick={() => preview && onImport?.(preview)}>{t('apply')}</Button>
        </>
      ) : null}
    </div>
  )
}
