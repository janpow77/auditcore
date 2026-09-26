import type { FormEvent } from 'react'
import { confidenceText, parameterUnit, samplingFieldError, type FieldError, type Locale, type MethodProfile, type ParameterSpec, type SamplingTranslate } from '@auditcore/ui-core'
import { Button } from '../base/Button'
import { classes, useElementId } from '../store'

export interface SamplingParametersProps {
  profile: MethodProfile
  errors: Readonly<Record<string, FieldError>>
  texts: Record<string, string>
  confidence: number | null
  busy?: boolean
  hasPopulation?: boolean
  t: SamplingTranslate
  locale: Locale
  onTextsChange: (texts: Record<string, string>) => void
  onConfidenceChange: (confidence: number | null) => void
  onCalculate: () => void
  onSuggest: () => void
}

function ConfidenceField({ profile, confidence, error, t, locale, onChange }: { profile: MethodProfile; confidence: number | null; error: string; t: SamplingTranslate; locale: Locale; onChange: (value: number | null) => void }) {
  return (
    <label className={classes('fa-sampling__field', !!error && 'fa-sampling__field--error')}>
      <span className="fa-sampling__label">{t('confidence')}</span>
      <select className="fa-sampling__select" data-testid="sampling-confidence" value={confidence ?? ''} aria-invalid={error ? 'true' : undefined} onChange={(event) => onChange(event.target.value === '' ? null : Number(event.target.value))}>
        <option value="">{t('choose')}</option>
        {profile.confidence_levels.map((level) => <option key={level.level} value={level.level}>{confidenceText(level, t, locale)}</option>)}
      </select>
      {error ? <span className="fa-sampling__error" role="alert">{error}</span> : null}
    </label>
  )
}

function NumberField({ spec, id, text, error, onChange }: { spec: ParameterSpec; id: string; text: string; error: string; onChange: (value: string) => void }) {
  return (
    <label className={classes('fa-sampling__field', !!error && 'fa-sampling__field--error')}>
      <span className="fa-sampling__label">{spec.label}</span>
      <span className="fa-sampling__input-wrap">
        <input
          className="fa-sampling__input"
          inputMode="decimal"
          data-testid={`sampling-${spec.key}`}
          value={text}
          aria-invalid={error ? 'true' : undefined}
          aria-describedby={error ? `${id}-${spec.key}-error` : undefined}
          onChange={(event) => onChange(event.target.value)}
        />
        <span className="fa-sampling__unit" aria-hidden="true">{parameterUnit(spec)}</span>
      </span>
      {error ? <span id={`${id}-${spec.key}-error`} className="fa-sampling__error" role="alert">{error}</span> : null}
    </label>
  )
}

/** Parameter und Konfidenzniveau mit Prüfung je Feld (wie `SamplingParameters.vue`). */
export function SamplingParameters(props: SamplingParametersProps) {
  const { profile, t, locale } = props
  const id = useElementId('fa-sampling-param')
  const errorText = (key: string): string => samplingFieldError(props.errors[key], t, locale)
  const submit = (event: FormEvent): void => {
    event.preventDefault()
    props.onCalculate()
  }
  return (
    <section className="fa-sampling__card" aria-labelledby={`${id}-title`}>
      <h3 id={`${id}-title`} className="fa-sampling__heading">{t('parameters')}</h3>
      <form className="fa-sampling__form" noValidate onSubmit={submit}>
        {profile.parameters.map((spec) =>
          spec.type === 'choice' ? (
            <ConfidenceField key={spec.key} profile={profile} confidence={props.confidence} error={errorText('confidence_level')} t={t} locale={locale} onChange={props.onConfidenceChange} />
          ) : (
            <NumberField key={spec.key} spec={spec} id={id} text={props.texts[spec.key] ?? ''} error={errorText(spec.key)} onChange={(value) => props.onTextsChange({ ...props.texts, [spec.key]: value })} />
          ),
        )}
        <div className="fa-sampling__actions">
          <Button variant="primary" type="submit" loading={props.busy} testId="sampling-calculate">{t('calculate')}</Button>
          {props.hasPopulation ? <Button variant="ghost" onClick={props.onSuggest}>{t('fromPopulation')}</Button> : null}
        </div>
      </form>
    </section>
  )
}
