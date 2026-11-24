import { redactionReportRows } from '@auditcore/ui-core'
import { Fragment } from 'react'
import { Button } from '../base/Button'
import type { UseRedaction } from './useRedaction'

/** Nachgeprüfter Bericht (nur Zahlen) und Download der geschwärzten PDF. */
export function RedactionResultView({ view, id }: { view: UseRedaction; id: string }) {
  const { state, controller, t, locale } = view
  const result = state.result
  if (!result) return null
  return (
    <section className="fa-redaction__card" aria-labelledby={`${id}-result`} aria-live="polite" data-testid="redaction-result">
      <h3 id={`${id}-result`} className="fa-redaction__heading">{t('resultHeading')}</h3>
      {result.report.verified ? <p className="fa-redaction__success">{t('verified')}</p> : null}
      <dl className="fa-redaction__report">
        {redactionReportRows(state, t, locale).map((row) => (
          <Fragment key={row.key}>
            <dt>{row.label}</dt>
            <dd data-report={row.key}>{row.value}</dd>
          </Fragment>
        ))}
      </dl>
      <div className="fa-redaction__actions">
        {state.resultUrl ? (
          <a className="fa-button fa-button--primary fa-button--md" href={state.resultUrl} download={result.filename} data-testid="redaction-download">
            <span className="fa-button__label">{t('download', { filename: result.filename })}</span>
          </a>
        ) : null}
        <Button testId="redaction-edit" onClick={() => controller.editAgain()}>{t('editAgain')}</Button>
        <Button variant="ghost" testId="redaction-reset" onClick={() => controller.reset()}>{t('another')}</Button>
      </div>
    </section>
  )
}
