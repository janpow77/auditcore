import type { ChangeEvent } from 'react'
import {
  COMPARISON_MODES,
  MAX_THRESHOLD,
  MIN_THRESHOLD,
  ROW_STATUSES,
  type CompareForm,
  type ComparisonsMessageKey,
  type ComparisonsTranslate,
  type ProfileOption,
  type RowStatus,
} from '@auditcore/ui-core'
import { classes, useElementId } from '../store'

export interface ComparisonOptionsProps {
  form: CompareForm
  t: ComparisonsTranslate
  profileOptions?: readonly ProfileOption[]
  thresholdError?: string
  sectionsError?: string
  onFormUpdate: (patch: Partial<CompareForm>) => void
  onSectionToggle: (status: RowStatus, enabled: boolean) => void
}

const FLAGS = ['includeAnswers', 'includeNotes', 'includeEditorial'] as const

function onThreshold(event: ChangeEvent<HTMLInputElement>, update: ComparisonOptionsProps['onFormUpdate']): void {
  const value = event.target.valueAsNumber
  update({ threshold: Number.isNaN(value) ? 0 : value })
}

function StandardRow({ form, t, thresholdError = '', onFormUpdate, id }: ComparisonOptionsProps & { id: string }) {
  return (
    <div className="fa-comparisons-form__row">
      <div className="fa-comparisons-form__field">
        <label htmlFor={`${id}-mode`}>{t('modeLabel')}</label>
        <select id={`${id}-mode`} value={form.mode} onChange={(event) => onFormUpdate({ mode: event.target.value as CompareForm['mode'] })}>
          {COMPARISON_MODES.map((mode) => <option key={mode} value={mode}>{t(`mode_${mode}` as ComparisonsMessageKey)}</option>)}
        </select>
      </div>
      <div className={classes('fa-comparisons-form__field', !!thresholdError && 'fa-comparisons-form__field--error')}>
        <label htmlFor={`${id}-threshold`}>{t('thresholdLabel')}</label>
        <input
          id={`${id}-threshold`} type="number" min={MIN_THRESHOLD} max={MAX_THRESHOLD} step="1" value={form.threshold}
          aria-invalid={thresholdError ? 'true' : undefined} aria-describedby={thresholdError ? `${id}-threshold-error` : undefined}
          onChange={(event) => onThreshold(event, onFormUpdate)}
        />
        {thresholdError ? <p id={`${id}-threshold-error`} className="fa-comparisons-form__error">{thresholdError}</p> : null}
      </div>
    </div>
  )
}

/** Optionen des Standardvergleichs, Ausgabeabschnitte und Profil (wie `ComparisonOptions.vue`). */
export function ComparisonOptions(props: ComparisonOptionsProps) {
  const { form, t, profileOptions = [], sectionsError = '', onFormUpdate } = props
  const id = useElementId('fa-comparisons-options')
  const standard = form.kind === 'standard'
  return (
    <div className="fa-comparisons-form__options">
      {standard ? <StandardRow {...props} id={id} /> : null}
      <fieldset className="fa-comparisons-form__group">
        <legend>{t('optionsLegend')}</legend>
        {standard ? FLAGS.map((flag) => (
          <label key={flag}><input type="checkbox" checked={form[flag]} onChange={(event) => onFormUpdate({ [flag]: event.target.checked })} /> {t(flag)}</label>
        )) : null}
        <label><input type="checkbox" checked={form.highlightWords} onChange={(event) => onFormUpdate({ highlightWords: event.target.checked })} /> {t('highlightWords')}</label>
      </fieldset>
      <fieldset className="fa-comparisons-form__group" aria-invalid={sectionsError ? 'true' : undefined} aria-describedby={sectionsError ? `${id}-sections-error` : undefined}>
        <legend>{t('sectionsLegend')}</legend>
        {ROW_STATUSES.map((status) => (
          <label key={status}>
            <input type="checkbox" checked={form.sections.includes(status)} onChange={(event) => props.onSectionToggle(status, event.target.checked)} /> {t(`section_${status}` as ComparisonsMessageKey)}
          </label>
        ))}
        {sectionsError ? <p id={`${id}-sections-error`} className="fa-comparisons-form__error">{sectionsError}</p> : null}
      </fieldset>
      {profileOptions.length > 1 ? (
        <div className="fa-comparisons-form__field">
          <label htmlFor={`${id}-profile`}>{t('profileLabel')}</label>
          <select id={`${id}-profile`} value={form.profile} onChange={(event) => onFormUpdate({ profile: event.target.value })}>
            {profileOptions.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
          </select>
        </div>
      ) : null}
    </div>
  )
}
