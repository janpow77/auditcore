import type { ChangeEvent, FormEvent } from 'react'
import { identifierColumnFields, identifierErrorKey, importOptionalColumn } from '@flowaudit/ui-core'
import { Button } from '../base/Button'
import { IdentifierBatchResult } from './IdentifierBatchResult'
import type { UseIdentifierCheck } from './useIdentifierCheck'

function Mapping({ view }: { view: UseIdentifierCheck }) {
  const { state, table, controller, t, kinds, mapping } = view
  const header = table.table?.header ?? []
  return (
    <>
      <label className="fa-ident__check">
        <input type="checkbox" checked={table.hasHeader} data-testid="ident-header" onChange={(event) => controller.setHasHeader(event.target.checked)} />
        {t('header')}
      </label>
      <label className="fa-ident__field">
        <span className="fa-ident__label">{t('kindSource')}</span>
        <select value={state.batchKind ?? ''} className="fa-ident__select" data-testid="ident-batch-kind" onChange={(event) => controller.setBatchKind(event.target.value || null)}>
          <option value="">{t('fromColumn')}</option>
          {kinds.map((entry) => <option key={entry.id} value={entry.id}>{entry.label}</option>)}
        </select>
      </label>
      {identifierColumnFields(mapping).map((field) => (
        <label key={field.id} className="fa-ident__field">
          <span className="fa-ident__label">{t(field.label)}</span>
          <select value={field.value ?? ''} className="fa-ident__select" data-testid={`ident-col-${field.id}`} onChange={(event) => controller.setColumn(field.id, importOptionalColumn(event.target.value))}>
            {field.placeholder ? <option value="">{t(field.placeholder)}</option> : null}
            {header.map((name, index) => <option key={index} value={index}>{name}</option>)}
          </select>
        </label>
      ))}
    </>
  )
}

/** Stapelprüfung aus einer Tabelle (wie `IdentifierBatch.vue`); die Datei liest der TableImport-Controller des Kerns. */
export function IdentifierBatch({ view, id }: { view: UseIdentifierCheck; id: string }) {
  const { state, table, controller, t } = view
  const onFile = async (event: ChangeEvent<HTMLInputElement>): Promise<void> => {
    const file = event.target.files?.[0]
    if (file) await controller.readFile(file)
  }
  const submit = (event: FormEvent): void => {
    event.preventDefault()
    void controller.checkBatch()
  }
  return (
    <section className="fa-ident__card" aria-labelledby={`${id}-batch`}>
      <h3 id={`${id}-batch`} className="fa-ident__heading">{t('batch')}</h3>
      <p className="fa-ident__muted">{t('batchHelp')}</p>
      <label htmlFor={`${id}-file`} className="fa-ident__label">{t('file')}</label>
      <input id={`${id}-file`} className="fa-ident__file" type="file" accept=".csv,.tsv,.txt,text/csv,text/plain" data-testid="ident-file" onChange={(event) => void onFile(event)} />
      {table.table ? (
        <form className="fa-ident__form" noValidate onSubmit={submit}>
          <p className="fa-ident__muted" aria-live="polite">{t('tableSummary', { file: table.filename, rows: table.table.rows.length })}</p>
          <Mapping view={view} />
          {state.batchValidation ? <p className="fa-ident__error" role="alert">{t(identifierErrorKey(state.batchValidation))}</p> : null}
          <Button variant="primary" type="submit" loading={state.busy === 'batch'} testId="ident-batch-run">{t('batchRun')}</Button>
        </form>
      ) : null}
      {state.batch ? <IdentifierBatchResult view={view} /> : null}
    </section>
  )
}
