import type { ChangeEvent, FormEvent } from 'react'
import { extractionAccept, extractionProfileText, extractionSizeText, extractionValidationText } from '@flowaudit/ui-core'
import { Button } from '../base/Button'
import type { UseExtraction } from './useExtraction'

/** Hochladen: Datei, Profil, Hinweise zu Größe, erprobendem Profil und Aufbewahrung. */
export function ExtractionForm({ view, id }: { view: UseExtraction; id: string }) {
  const { state, controller, t, locale } = view
  const catalogue = state.catalogue
  if (!catalogue) return null
  const profile = catalogue.profiles.find((entry) => entry.id === state.profileId) ?? null
  const problem = state.validation ? extractionValidationText(state.validation, catalogue, t, locale) : ''
  const onSubmit = (event: FormEvent): void => {
    event.preventDefault()
    void controller.extract()
  }
  const onFile = (event: ChangeEvent<HTMLInputElement>): void => controller.selectFile(event.target.files?.[0] ?? null)
  return (
    <form className="fa-extraction__card" noValidate aria-labelledby={`${id}-upload`} onSubmit={onSubmit}>
      <h3 id={`${id}-upload`} className="fa-extraction__heading">{t('upload')}</h3>
      <div className="fa-extraction__form">
        <label className="fa-extraction__field">
          <span className="fa-extraction__label">{t('file')}</span>
          <input className="fa-extraction__file" type="file" accept={extractionAccept(catalogue)} data-testid="extraction-file" onChange={onFile} />
        </label>
        <label className="fa-extraction__field">
          <span className="fa-extraction__label">{t('profile')}</span>
          <select className="fa-extraction__input" value={state.profileId ?? ''} data-testid="extraction-profile" onChange={(event) => controller.setProfile(event.target.value || null)}>
            {catalogue.profiles.map((entry) => (
              <option key={entry.id} value={entry.id} disabled={!entry.available}>{extractionProfileText(entry, t)}</option>
            ))}
          </select>
        </label>
      </div>
      <p className="fa-extraction__muted">{t('fileHelp', { size: extractionSizeText(catalogue.limits.max_upload_bytes, locale) })}</p>
      {profile?.status === 'EXPERIMENTAL' ? <p className="fa-extraction__muted" data-testid="extraction-experimental">{t('experimental')}</p> : null}
      <p className="fa-extraction__muted">{t('retention')}</p>
      {problem ? <p className="fa-extraction__error" role="alert">{problem}</p> : null}
      <div>
        <Button variant="primary" type="submit" loading={state.busy === 'run'} testId="extraction-run">{t('run')}</Button>
      </div>
    </form>
  )
}
