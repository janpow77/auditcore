import { useEffect, useRef, useState } from 'react'
import {
  ATTRIBUTE_FIELDS,
  attributesApproachChoices,
  attributesConclusionTone,
  attributesConfidenceChoices,
  attributesFieldLabel,
  attributesFormMessage,
  attributesIssueKey,
  attributesMessages,
  attributesMetrics,
  attributesPercent,
  attributesStepColumns,
  attributesStepRows,
  createAttributesController,
  type AttributeApproach,
  type AttributesController,
  type AttributesData,
  type AttributesPort,
  type AttributesResult,
  type AttributesTranslate,
  type Locale,
} from '@auditcore/ui-core'
import { Badge } from '../base/Badge'
import { Button } from '../base/Button'
import { useTranslation } from '../i18n'
import { useElementId, useStoreState } from '../store'
import { FlowauditTable } from '../table/FlowauditTable'

export interface FlowauditAttributeSamplingProps {
  port?: AttributesPort | null
  locale?: Locale
  onEvaluationCompleted?: (result: AttributesResult) => void
  onError?: (message: string) => void
}

interface FormProps {
  state: AttributesData
  controller: AttributesController
  t: AttributesTranslate
  locale: Locale
}

function Form({ state, controller, t, locale }: FormProps) {
  const issue = (key: string): string => {
    const found = state.issues[key]
    return found ? t(attributesIssueKey(found)) : ''
  }
  return (
    <div className="fa-attributes__form">
      <label className="fa-attributes__field">
        <span className="fa-attributes__label">{t('approach')}</span>
        <select className="fa-attributes__select" value={state.form.approach} data-testid="attributes-approach" onChange={(event) => controller.update({ approach: event.target.value as AttributeApproach })}>
          {attributesApproachChoices(t).map((entry) => <option key={entry.id} value={entry.id}>{entry.label}</option>)}
        </select>
      </label>
      {ATTRIBUTE_FIELDS.map((field) => (
        <label key={field.key} className="fa-attributes__field">
          <span className="fa-attributes__label">{attributesFieldLabel(field.key, state.form.approach, t)}</span>
          <input className="fa-attributes__input" inputMode="decimal" value={state.form[field.key]} aria-invalid={issue(field.key) ? 'true' : undefined} data-testid={`attributes-${field.key}`} onChange={(event) => controller.update({ [field.key]: event.target.value })} />
          {issue(field.key) ? <span className="fa-attributes__error">{issue(field.key)}</span> : null}
        </label>
      ))}
      <label className="fa-attributes__field">
        <span className="fa-attributes__label">{t('confidence')}</span>
        <select className="fa-attributes__select" value={state.form.confidence === null ? '' : String(state.form.confidence)} aria-invalid={issue('confidence') ? 'true' : undefined} data-testid="attributes-confidence" onChange={(event) => controller.update({ confidence: event.target.value === '' ? null : Number(event.target.value) })}>
          <option value="">{t('choose')}</option>
          {attributesConfidenceChoices(state.catalogue).map((level) => <option key={level} value={String(level)}>{attributesPercent(level, locale)}</option>)}
        </select>
      </label>
      {state.form.approach === 'normal' ? (
        <label className="fa-attributes__field">
          <span className="fa-attributes__label">{t('factorProfile')}</span>
          <select className="fa-attributes__select" value={state.form.profileId ?? ''} data-testid="attributes-profile" onChange={(event) => controller.update({ profileId: event.target.value || null })}>
            <option value="">{t('choose')}</option>
            {(state.catalogue?.factor_profiles ?? []).map((entry) => <option key={entry.id} value={entry.id}>{entry.label}</option>)}
          </select>
        </label>
      ) : null}
    </div>
  )
}

function Result({ result, t, locale, tableLocale }: { result: AttributesResult; t: AttributesTranslate; locale: Locale; tableLocale?: Locale }) {
  const conclusion = result.attributes.conclusion
  return (
    <>
      <h4 className="fa-attributes__heading">{t('resultTitle')}</h4>
      <p><Badge tone={attributesConclusionTone(conclusion)} testId="attributes-conclusion">{t(`conclusion${conclusion}`)}</Badge></p>
      <dl className="fa-attributes__metrics" data-testid="attributes-metrics">
        {attributesMetrics(result, t, locale).map((metric) => (
          <div key={metric.id} className="fa-attributes__metric" data-metric={metric.id}>
            <dt>{metric.label}</dt>
            <dd>{metric.value}</dd>
          </div>
        ))}
      </dl>
      <details>
        <summary>{t('derivation')}</summary>
        <FlowauditTable columns={attributesStepColumns(t, locale)} rows={attributesStepRows(result)} caption={t('derivation')} locale={tableLocale} testId="attributes-steps" />
      </details>
      <p className="fa-attributes__muted">{`${t('fingerprint')}: ${result.fingerprint}`}</p>
    </>
  )
}

/**
 * Merkmalsstichprobe für Systemprüfungen als native React-Komponente (Vertrag wie
 * `<flowaudit-attribute-sampling>`; Leitfaden 7.9, Discovery und Stop-or-go 7.9.6).
 * Ereignisse: `onEvaluationCompleted`, `onError`.
 */
export function FlowauditAttributeSampling(props: FlowauditAttributeSamplingProps) {
  const { t, locale } = useTranslation(attributesMessages, props.locale)
  const latest = useRef(props)
  latest.current = props
  const [controller] = useState(() =>
    createAttributesController({
      port: () => latest.current.port ?? null,
      callbacks: () => ({
        evaluated: (result) => latest.current.onEvaluationCompleted?.(result),
        failed: (message) => latest.current.onError?.(message),
      }),
    }),
  )
  const state = useStoreState(controller.store)
  const id = useElementId('fa-attributes')
  useEffect(() => {
    void controller.load()
  }, [controller, props.port])
  const message = attributesFormMessage(state.issues, t)
  return (
    <section className="fa-attributes" lang={locale} aria-labelledby={`${id}-title`}>
      <h3 id={`${id}-title`} className="fa-attributes__heading">{t('title')}</h3>
      {state.busy === 'load' ? <p className="fa-attributes__muted" role="status">{t('loading')}</p> : null}
      {state.error ? <p className="fa-attributes__failure" role="alert">{t('failed', { message: state.error })}</p> : null}
      {state.catalogue ? (
        <>
          <p className="fa-attributes__muted">{t('notice')}</p>
          <Form state={state} controller={controller} t={t} locale={locale} />
          <div className="fa-attributes__actions">
            <Button variant="primary" loading={state.busy === 'evaluate'} testId="attributes-evaluate" onClick={() => void controller.evaluate()}>{t('evaluate')}</Button>
            {message ? <p className="fa-attributes__error" role="alert">{message}</p> : null}
          </div>
          {state.result ? <Result result={state.result} t={t} locale={locale} tableLocale={props.locale} /> : null}
        </>
      ) : null}
    </section>
  )
}
