import { samplesizeStrataColumns, type Locale, type SamplesizeController, type SamplesizeData, type SamplesizeMessageKey, type StratumColumn, type Translate } from '@auditcore/ui-core'

/** Was die Teilkomponenten des Planers brauchen. */
export interface SampleSizeView {
  controller: SamplesizeController
  state: SamplesizeData
  t: Translate<SamplesizeMessageKey>
  locale: Locale
}

function Cell({ view, column, index }: { view: SampleSizeView; column: { key: StratumColumn; label: string }; index: number }) {
  const { controller, state, t } = view
  const row = state.form.strata[index]
  const label = t('stratumRow', { column: column.label, row: index + 1 })
  if (!row) return null
  if (column.key === 'exhaustive') {
    return <td><input type="checkbox" checked={row.exhaustive} aria-label={label} onChange={(event) => controller.setStratum(index, { exhaustive: event.target.checked })} /></td>
  }
  const key = column.key
  return (
    <td>
      <input className="fa-samplesize__input" inputMode={key === 'name' ? undefined : 'decimal'} value={row[key]} aria-label={label} onChange={(event) => controller.setStratum(index, { [key]: event.target.value })} />
    </td>
  )
}

/** Schichten des Planers (wie `SampleSizeStrata.vue`). */
export function SampleSizeStrata({ view }: { view: SampleSizeView }) {
  const { controller, state, t } = view
  const columns = samplesizeStrataColumns(state, t)
  return (
    <fieldset className="fa-samplesize__strata">
      <legend className="fa-samplesize__label">{t('strata')}</legend>
      <table className="fa-samplesize__table" data-testid="samplesize-strata">
        <thead>
          <tr>
            {columns.map((column) => <th key={column.key} scope="col">{column.label}</th>)}
            <td />
          </tr>
        </thead>
        <tbody>
          {state.form.strata.map((_, index) => (
            <tr key={index}>
              {columns.map((column) => <Cell key={column.key} view={view} column={column} index={index} />)}
              <td>
                <button type="button" className="fa-samplesize__remove" aria-label={t('removeStratum', { row: index + 1 })} onClick={() => controller.removeStratum(index)}>×</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <button type="button" className="fa-samplesize__add" onClick={() => controller.addStratum()}>{t('addStratum')}</button>
    </fieldset>
  )
}
