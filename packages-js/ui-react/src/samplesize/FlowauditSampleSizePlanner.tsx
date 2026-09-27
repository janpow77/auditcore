import { useEffect, useRef, useState } from 'react'
import { createSamplesizeController, hasFiniteCorrection, hasStrata, samplesizeFields, samplesizeMessages, samplesizeMethod, type Locale, type SampleSizePlan, type SampleSizeRequest, type SamplesizeFieldView, type SamplesizePort } from '@auditcore/ui-core'
import { useTranslation } from '../i18n'
import { useStoreState } from '../store'
import { SampleSizeResult } from './SampleSizeResult'
import { SampleSizeStrata, type SampleSizeView } from './SampleSizeStrata'

export interface FlowauditSampleSizePlannerProps {
  port?: SamplesizePort | null
  /** Vorbelegung des Formulars (Anfrage des Vertrags `auditcore_sampling.guidance/1`). */
  request?: SampleSizeRequest | null
  locale?: Locale
  onPlanCalculated?: (plan: SampleSizePlan) => void
  onError?: (message: string) => void
}

function Field({ view, field }: { view: SampleSizeView; field: SamplesizeFieldView }) {
  const { controller, t } = view
  const invalid = field.issue ? 'true' : undefined
  const testId = `samplesize-${field.key}`
  return (
    <label className="fa-samplesize__field">
      <span className="fa-samplesize__label">{field.label}</span>
      {field.kind === 'choice' ? (
        <select className="fa-samplesize__select" value={field.value} aria-invalid={invalid} data-testid={testId} onChange={(event) => controller.setValue(field.key, event.target.value)}>
          {field.key !== 'assurance_level' ? <option value="">{t('choose')}</option> : null}
          {field.options.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
        </select>
      ) : (
        <input className="fa-samplesize__input" inputMode={field.inputMode} value={field.value} aria-invalid={invalid} data-testid={testId} onChange={(event) => controller.setValue(field.key, event.target.value)} />
      )}
      {field.issue ? <span className="fa-samplesize__error">{field.issue}</span> : null}
    </label>
  )
}

function PlannerForm({ view }: { view: SampleSizeView }) {
  const { state, controller, t, locale } = view
  const catalogue = state.catalogue
  if (!catalogue) return null
  const method = samplesizeMethod(state)
  const fields = samplesizeFields(state, t, locale)
  return (
    <form className="fa-samplesize__form" noValidate onSubmit={(event) => { event.preventDefault(); void controller.calculate() }}>
      <label className="fa-samplesize__field">
        <span className="fa-samplesize__label">{t('method')}</span>
        <select className="fa-samplesize__select" value={state.form.methodId} data-testid="samplesize-method" onChange={(event) => controller.selectMethod(event.target.value)}>
          <option value="">{t('choose')}</option>
          {catalogue.methods.map((entry) => <option key={entry.id} value={entry.id}>{entry.label}</option>)}
        </select>
      </label>
      {method ? (
        <details className="fa-samplesize__source">
          <summary>{t('source')}</summary>
          <p>{catalogue.status_label} · {method.source}</p>
          <code>{method.formula}</code>
        </details>
      ) : null}
      {fields.length ? <div className="fa-samplesize__fields">{fields.map((field) => <Field key={field.key} view={view} field={field} />)}</div> : null}
      {hasFiniteCorrection(method) ? (
        <label className="fa-samplesize__check">
          <input type="checkbox" checked={state.form.finiteCorrection} data-testid="samplesize-fpc" onChange={(event) => controller.setFiniteCorrection(event.target.checked)} />
          <span>{t('finite_population_correction')}</span>
        </label>
      ) : null}
      {hasStrata(method) ? <SampleSizeStrata view={view} /> : null}
      {method ? <button type="submit" className="fa-samplesize__submit" data-testid="samplesize-calculate" disabled={state.busy !== null}>{t('calculate')}</button> : null}
    </form>
  )
}

/**
 * Stichprobenumfang nach KOM-Leitfaden als native React-Komponente (Vertrag wie
 * `<flowaudit-sample-size-planner>`). Ereignisse: `onPlanCalculated`, `onError`.
 */
export function FlowauditSampleSizePlanner(props: FlowauditSampleSizePlannerProps) {
  const { t, locale } = useTranslation(samplesizeMessages, props.locale)
  const latest = useRef(props)
  latest.current = props
  const [controller] = useState(() =>
    createSamplesizeController({
      port: () => latest.current.port ?? null,
      request: () => latest.current.request ?? null,
      callbacks: () => ({
        planned: (plan) => latest.current.onPlanCalculated?.(plan),
        failed: (message) => latest.current.onError?.(message),
      }),
    }),
  )
  const state = useStoreState(controller.store)
  useEffect(() => {
    void controller.load()
  }, [controller, props.port, props.request])
  const view: SampleSizeView = { controller, state, t, locale }
  return (
    <section className="fa-samplesize" lang={locale} aria-label={t('title')}>
      {state.busy ? <p className="fa-samplesize__muted" role="status">{t(state.busy === 'load' ? 'loading' : 'calculating')}</p> : null}
      {state.error ? <p className="fa-samplesize__failure" role="alert">{t('failed', { message: state.error })}</p> : null}
      <PlannerForm view={view} />
      {state.plan ? <SampleSizeResult plan={state.plan} t={t} locale={locale} /> : null}
    </section>
  )
}
