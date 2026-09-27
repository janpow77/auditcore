import type { ChangeEvent, FormEvent } from 'react'
import type { DecimalSeparator } from '@auditcore/common'
import { batchchecksColumnFields, batchchecksHasTable, batchchecksSourceText, importOptionalColumn } from '@auditcore/ui-core'
import { Button } from '../base/Button'
import type { UseBatchChecks } from './useBatchChecks'

/** Spaltenzuordnung der Tabelle (wie der `fieldset` in `BatchChecksInput.vue`). */
function Columns({ view }: { view: UseBatchChecks }) {
  const { state, table, controller, t } = view
  const header = table.table?.header ?? []
  return (
    <fieldset className="fa-batchchecks__card">
      <legend className="fa-batchchecks__subheading">{t('columns')}</legend>
      <label className="fa-batchchecks__check">
        <input type="checkbox" checked={table.hasHeader} data-testid="batchchecks-header" onChange={(event) => controller.setHasHeader(event.target.checked)} />
        {t('header')}
      </label>
      <div className="fa-batchchecks__grid">
        <label className="fa-batchchecks__field">
          <span className="fa-batchchecks__label">{t('decimal')}</span>
          <select className="fa-batchchecks__input" value={table.decimal} data-testid="batchchecks-decimal" onChange={(event) => controller.setDecimal(event.target.value as DecimalSeparator)}>
            <option value=",">{t('decimalComma')}</option>
            <option value=".">{t('decimalDot')}</option>
          </select>
        </label>
        {batchchecksColumnFields(state).map((field) => (
          <label key={field.name} className="fa-batchchecks__field">
            <span className="fa-batchchecks__label">{field.label}</span>
            <select className="fa-batchchecks__input" value={field.value ?? ''} data-testid={`batchchecks-col-${field.name}`} onChange={(event) => controller.setColumn(field.name, importOptionalColumn(event.target.value))}>
              <option value="">{t('none')}</option>
              {header.map((name, index) => <option key={index} value={index}>{name}</option>)}
            </select>
          </label>
        ))}
      </div>
    </fieldset>
  )
}

/** Bestand einlesen: Datei, Zuordnung, Gesamtvolumen, Ergänzungsprüfungen (wie `BatchChecksInput.vue`). */
export function BatchChecksInput({ view, id }: { view: UseBatchChecks; id: string }) {
  const { state, table, controller, t } = view
  const max = state.catalogue?.limits.max_documents ?? 0
  const source = batchchecksSourceText(state, table, t)
  const onFile = async (event: ChangeEvent<HTMLInputElement>): Promise<void> => {
    const file = event.target.files?.[0]
    if (file) await controller.readFile(file)
  }
  const onSubmit = (event: FormEvent): void => {
    event.preventDefault()
    void controller.check()
  }
  return (
    <form className="fa-batchchecks__card" noValidate aria-labelledby={`${id}-input`} onSubmit={onSubmit}>
      <h3 id={`${id}-input`} className="fa-batchchecks__heading">{t('input')}</h3>
      <label className="fa-batchchecks__field">
        <span className="fa-batchchecks__label">{t('file')}</span>
        <input className="fa-batchchecks__file" type="file" accept=".csv,.tsv,.txt,.json,text/csv,text/plain,application/json" data-testid="batchchecks-file" onChange={(event) => void onFile(event)} />
      </label>
      <p className="fa-batchchecks__muted">{t('fileHelp', { max })}</p>
      {source ? <p className="fa-batchchecks__muted" aria-live="polite" data-testid="batchchecks-source">{source}</p> : null}
      {batchchecksHasTable(state, table) ? <Columns view={view} /> : null}
      <div className="fa-batchchecks__grid">
        <label className="fa-batchchecks__field">
          <span className="fa-batchchecks__label">{t('totalVolume')}</span>
          <input className="fa-batchchecks__input" type="text" inputMode="decimal" value={state.totalVolume} data-testid="batchchecks-total" onChange={(event) => controller.setTotalVolume(event.target.value)} />
        </label>
        <label className="fa-batchchecks__check">
          <input type="checkbox" checked={state.supplementary} data-testid="batchchecks-supplementary" onChange={(event) => controller.setSupplementary(event.target.checked)} />
          {t('supplementary')}
        </label>
      </div>
      <p className="fa-batchchecks__muted">{t('totalVolumeHelp')}</p>
      {state.validation ? <p className="fa-batchchecks__error" role="alert">{t(`error${state.validation}`, { max })}</p> : null}
      <div>
        <Button variant="primary" type="submit" loading={state.busy === 'run'} testId="batchchecks-run">{t('run')}</Button>
      </div>
    </form>
  )
}
