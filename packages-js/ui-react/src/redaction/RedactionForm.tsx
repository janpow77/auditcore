import type { ChangeEvent, FormEvent } from 'react'
import { redactionPatternText, redactionSizeText, redactionValidationText } from '@auditcore/ui-core'
import { Button } from '../base/Button'
import type { UseRedaction } from './useRedaction'

/** Datei, Muster, eigene Begriffe und Suchoptionen. */
export function RedactionForm({ view, id }: { view: UseRedaction; id: string }) {
  const { state, controller, t, locale } = view
  const catalogue = state.catalogue
  if (!catalogue) return null
  const problem = redactionValidationText(state.validation, catalogue, t, locale, state.fileFixed)
  const onSubmit = (event: FormEvent): void => {
    event.preventDefault()
    void controller.plan()
  }
  const onFile = (event: ChangeEvent<HTMLInputElement>): void => controller.selectFile(event.target.files?.[0] ?? null)
  return (
    <form className="fa-redaction__card" noValidate aria-labelledby={`${id}-form`} data-testid="redaction-form" onSubmit={onSubmit}>
      <h3 id={`${id}-form`} className="fa-redaction__heading" tabIndex={-1}>{t('formHeading')}</h3>
      {state.fileFixed ? (
        <p id={`${id}-file-provided`} className="fa-redaction__field fa-redaction__provided" data-testid="redaction-file-provided">
          <span className="fa-redaction__label">{t('fileProvided')}</span>
          <span className="fa-redaction__value">{state.filename}</span>
        </p>
      ) : (
        <>
          <label className="fa-redaction__field">
            <span className="fa-redaction__label">{t('file')}</span>
            <input className="fa-redaction__file" type="file" accept="application/pdf,.pdf" aria-describedby={`${id}-file-help`} data-testid="redaction-file" onChange={onFile} />
          </label>
          {state.filename ? <p className="fa-redaction__muted" data-testid="redaction-file-chosen">{t('fileChosen', { name: state.filename })}</p> : null}
          <p id={`${id}-file-help`} className="fa-redaction__muted">{t('fileHelp', { size: redactionSizeText(catalogue.limits.max_upload_bytes, locale), pages: catalogue.limits.max_pages })}</p>
        </>
      )}
      <fieldset className="fa-redaction__patterns" aria-describedby={state.fileFixed ? `${id}-file-provided` : undefined}>
        <legend className="fa-redaction__label">{t('patterns')}</legend>
        {catalogue.patterns.map((pattern) => (
          <label key={pattern.id} className="fa-redaction__check" title={pattern.hint}>
            <input type="checkbox" data-pattern={pattern.id} checked={state.patterns.includes(pattern.id)} disabled={!pattern.available} onChange={(event) => controller.setPattern(pattern.id, event.target.checked)} />
            <span>{redactionPatternText(pattern, t)}</span>
          </label>
        ))}
      </fieldset>
      <label className="fa-redaction__field">
        <span className="fa-redaction__label">{t('terms')}</span>
        <textarea className="fa-redaction__input" rows={4} aria-describedby={`${id}-terms-help`} data-testid="redaction-terms" value={state.terms} onChange={(event) => controller.setTerms(event.target.value)} />
      </label>
      <p id={`${id}-terms-help`} className="fa-redaction__muted">{t('termsHelp', { count: catalogue.limits.max_terms, length: catalogue.limits.max_term_length })}</p>
      <div className="fa-redaction__options">
        <label className="fa-redaction__check">
          <input type="checkbox" data-testid="redaction-case" checked={state.caseSensitive} onChange={(event) => controller.setOption('caseSensitive', event.target.checked)} />
          <span>{t('caseSensitive')}</span>
        </label>
        <label className="fa-redaction__check">
          <input type="checkbox" data-testid="redaction-whole-word" checked={state.wholeWord} onChange={(event) => controller.setOption('wholeWord', event.target.checked)} />
          <span>{t('wholeWord')}</span>
        </label>
      </div>
      {problem ? <p className="fa-redaction__error" role="alert">{problem}</p> : null}
      <div>
        <Button variant="primary" type="submit" loading={state.busy === 'plan'} testId="redaction-search">{t('search')}</Button>
      </div>
    </form>
  )
}
