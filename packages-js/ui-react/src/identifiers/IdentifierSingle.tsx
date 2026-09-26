import type { FormEvent } from 'react'
import { identifierErrorKey, kindNeedsCountry } from '@auditcore/ui-core'
import { Button } from '../base/Button'
import { IdentifierResultView } from './IdentifierResultView'
import type { UseIdentifierCheck } from './useIdentifierCheck'

function CountryField({ view, id }: { view: UseIdentifierCheck; id: string }) {
  const { state, controller, t } = view
  if (!kindNeedsCountry(state.catalogue, state.kind)) return null
  return (
    <label className="fa-ident__field">
      <span className="fa-ident__label">{t('country')}</span>
      <input value={state.country} className="fa-ident__input fa-ident__input--short" autoComplete="off" maxLength={3} aria-describedby={`${id}-country`} data-testid="ident-country" onChange={(event) => controller.setField('country', event.target.value)} />
      <span id={`${id}-country`} className="fa-ident__muted">{t('countryHelp')}</span>
    </label>
  )
}

/** Einzelprüfung: Kennungsart, Wert, ggf. Land; Ergebnis mit Begründung (wie `IdentifierSingle.vue`). */
export function IdentifierSingle({ view, id }: { view: UseIdentifierCheck; id: string }) {
  const { state, controller, t, kinds } = view
  const catalogue = state.catalogue
  if (!catalogue) return null
  const kindInfo = kinds.find((entry) => entry.id === state.kind) ?? null
  const submit = (event: FormEvent): void => {
    event.preventDefault()
    void controller.check()
  }
  return (
    <section className="fa-ident__card" aria-labelledby={`${id}-single`}>
      <h3 id={`${id}-single`} className="fa-ident__heading">{t('single')}</h3>
      <form className="fa-ident__form" noValidate onSubmit={submit}>
        <label className="fa-ident__field">
          <span className="fa-ident__label">{t('kind')}</span>
          <select value={state.kind ?? ''} className="fa-ident__select" data-testid="ident-kind" onChange={(event) => controller.setKind(event.target.value || null)}>
            <option value="">{t('choose')}</option>
            {kinds.map((entry) => <option key={entry.id} value={entry.id}>{entry.label}</option>)}
          </select>
        </label>
        {kindInfo ? <p className="fa-ident__muted">{kindInfo.description}</p> : null}
        <label className="fa-ident__field">
          <span className="fa-ident__label">{t('value')}</span>
          <input value={state.value} className="fa-ident__input" autoComplete="off" spellCheck={false} maxLength={catalogue.limits.max_value_length} data-testid="ident-value" onChange={(event) => controller.setField('value', event.target.value)} />
        </label>
        <CountryField view={view} id={id} />
        {state.validation ? <p className="fa-ident__error" role="alert">{t(identifierErrorKey(state.validation))}</p> : null}
        <Button variant="primary" type="submit" loading={state.busy === 'check'} testId="ident-check">{t('check')}</Button>
      </form>
      {state.result ? <IdentifierResultView view={view} result={state.result} /> : null}
    </section>
  )
}
