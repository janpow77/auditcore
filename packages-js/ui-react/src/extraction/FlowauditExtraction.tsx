import { Fragment } from 'react'
import {
  extractionDocumentText,
  extractionFieldThreshold,
  extractionOcrText,
  extractionStatusText,
  extractionStatusTone,
  type ExtractionRun,
} from '@auditcore/ui-core'
import { Badge } from '../base/Badge'
import { useElementId } from '../store'
import { ExtractionForm } from './ExtractionForm'
import { ExtractionFields, ExtractionFindings } from './ExtractionTables'
import { useExtraction, type ExtractionInputs, type UseExtraction } from './useExtraction'

export type FlowauditExtractionProps = ExtractionInputs

function Result({ view, result, id }: { view: UseExtraction; result: ExtractionRun; id: string }) {
  const { t, locale } = view
  const run = result.run
  return (
    <section className="fa-extraction__card" aria-labelledby={`${id}-result`} aria-live="polite" data-testid="extraction-result">
      <h3 id={`${id}-result`} className="fa-extraction__heading">{`${t('result')} `}<Badge tone={extractionStatusTone(result)} testId="extraction-status">{extractionStatusText(result, t)}</Badge></h3>
      <p className="fa-extraction__notice">{t('notice')}</p>
      {run.error_code ? <p className="fa-extraction__failure" role="alert">{t('runError', { code: run.error_code, message: run.error ?? '' })}</p> : null}
      {run.retryable ? <p className="fa-extraction__muted">{t('retryable')}</p> : null}
      <dl className="fa-extraction__summary">
        <dt>{t('document')}</dt>
        <dd>{extractionDocumentText(result, t)}</dd>
        <dt>{t('ocr')}</dt>
        <dd data-testid="extraction-ocr">{extractionOcrText(result, t, locale)}</dd>
        <dt>{t('profile')}</dt>
        <dd>{`${result.profile.id} ${result.profile.version}`}</dd>
      </dl>
      <ExtractionFields fields={result.fields} threshold={extractionFieldThreshold(view.state.catalogue, result)} t={t} locale={locale} />
      <ExtractionFindings findings={result.findings} flags={result.flags} t={t} />
      {result.pages.length ? (
        <details className="fa-extraction__pages">
          <summary>{t('pagesText')}</summary>
          {result.pages.map((page) => (
            <Fragment key={page.page}>
              <h4 className="fa-extraction__label">{t('pageLabel', { page: page.page })}</h4>
              <pre className="fa-extraction__text">{page.text}</pre>
            </Fragment>
          ))}
        </details>
      ) : null}
    </section>
  )
}

/**
 * Belegerkennung als native React-Komponente (Vertrag wie `<flowaudit-extraction>`):
 * Dokument hochladen, Profil wählen, erkannte Felder mit Konfidenz und
 * Validierungsbefunde. Ereignisse: `onExtractionCompleted`, `onError`.
 */
export function FlowauditExtraction(props: FlowauditExtractionProps) {
  const view = useExtraction(props)
  const { state, t } = view
  const id = useElementId('fa-extraction')
  return (
    <div className="fa-extraction" lang={view.locale} data-testid="extraction">
      {!props.port ? <p className="fa-extraction__muted">{t('noPort')}</p> : null}
      {state.busy === 'load' ? <p className="fa-extraction__muted" role="status">{t('loading')}</p> : null}
      {state.error ? <p className="fa-extraction__failure" role="alert">{t('failed', { message: state.error })}</p> : null}
      {state.catalogue && !state.catalogue.enabled ? <p className="fa-extraction__notice" data-testid="extraction-disabled">{t('disabled')}</p> : null}
      {state.catalogue?.enabled ? <ExtractionForm view={view} id={id} /> : null}
      {state.result ? <Result view={view} result={state.result} id={id} /> : null}
    </div>
  )
}
