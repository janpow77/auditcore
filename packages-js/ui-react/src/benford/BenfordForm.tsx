import type { FormEvent } from 'react'
import { analyseErrorKey, needsShortValues, type BenfordTest, type ShortValues } from '@auditcore/ui-core'
import { Button } from '../base/Button'
import type { UseBenford } from './useBenford'

/** Test, Regel für kurze Werte und Bewertungsprofil (Formular aus `BenfordPanel.vue`). */
export function BenfordForm({ view, id }: { view: UseBenford; id: string }) {
  const { state, controller, t, profile } = view
  const catalogue = state.catalogue
  if (!catalogue) return null
  const submit = (event: FormEvent): void => {
    event.preventDefault()
    void controller.analyse()
  }
  return (
    <form className="fa-benford__card fa-benford__form" noValidate onSubmit={submit}>
      <label className="fa-benford__field">
        <span className="fa-benford__label">{t('test')}</span>
        <select value={state.test ?? ''} className="fa-benford__select" data-testid="benford-test" onChange={(event) => controller.setTest(event.target.value as BenfordTest)}>
          {catalogue.tests.map((entry) => <option key={entry.id} value={entry.id}>{entry.label}</option>)}
        </select>
      </label>
      {needsShortValues(catalogue, state.test) ? (
        <fieldset className="fa-benford__fieldset">
          <legend className="fa-benford__label">{t('shortValues')}</legend>
          {catalogue.short_values.map((option) => (
            <label key={option.id} className="fa-benford__radio">
              <input type="radio" checked={state.shortValues === option.id} name={`${id}-short`} value={option.id} data-testid={`benford-short-${option.id}`} onChange={() => controller.setShortValues(option.id as ShortValues)} />
              {option.label}
            </label>
          ))}
        </fieldset>
      ) : null}
      <label className="fa-benford__field">
        <span className="fa-benford__label">{t('profile')}</span>
        <select value={state.profileId ?? ''} className="fa-benford__select" data-testid="benford-profile" onChange={(event) => controller.setProfile(event.target.value || null)}>
          <option value="">{t('choose')}</option>
          {catalogue.profiles.map((entry) => <option key={entry.id} value={entry.id}>{entry.label}</option>)}
        </select>
      </label>
      {profile ? (
        <details className="fa-benford__source">
          <summary>{t('profileSource')}</summary>
          <p>{profile.source}</p>
          <p>{profile.note}</p>
        </details>
      ) : null}
      {state.validation ? <p className="fa-benford__error" role="alert">{t(analyseErrorKey(state.validation))}</p> : null}
      <Button variant="primary" type="submit" loading={state.busy === 'analyse'} testId="benford-analyse">{t('analyse')}</Button>
    </form>
  )
}
