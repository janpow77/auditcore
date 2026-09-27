import { confidenceChoices, extrapolationConfidenceLabel, extrapolationDesignChoices, extrapolationIssueText, extrapolationMethodGroups, systemAssessmentChoices, type ExtrapolationDesign } from '@auditcore/ui-core'
import { classes, useElementId } from '../store'
import type { UseExtrapolation } from './useExtrapolation'

type NumberKey = 'sampleSize' | 'materiality' | 'populationUnits'

function NumberField({ view, field, label, hint, testId }: { view: UseExtrapolation; field: NumberKey; label: string; hint: string; testId: string }) {
  const { state, controller, t } = view
  const issue = extrapolationIssueText(state.issues, field, t)
  const changes: Readonly<Record<NumberKey, (value: string) => void>> = { sampleSize: controller.setSampleSize, materiality: controller.setMateriality, populationUnits: controller.setPopulationUnits }
  const change = changes[field]
  return (
    <label className="fa-extrapolation__field">
      <span className="fa-extrapolation__label">{label}</span>
      <input className={classes('fa-extrapolation__input', 'fa-extrapolation__input--number')} inputMode={field === 'materiality' ? 'decimal' : 'numeric'} value={state.form[field]} aria-invalid={issue ? 'true' : undefined} data-testid={testId} onChange={(event) => change(event.target.value)} />
      {issue ? <span className="fa-extrapolation__error">{issue}</span> : null}
      <span className="fa-extrapolation__hint">{hint}</span>
    </label>
  )
}

function StatisticalFields({ view }: { view: UseExtrapolation }) {
  const { state, controller, t, method } = view
  const catalogue = state.catalogue
  if (!catalogue || !method?.statistical) return null
  return (
    <>
      <label className="fa-extrapolation__field">
        <span className="fa-extrapolation__label">{t('confidence')}</span>
        <select className="fa-extrapolation__select" value={state.form.confidence === null ? '' : String(state.form.confidence)} data-testid="extrapolation-confidence" onChange={(event) => controller.setConfidence(event.target.value === '' ? null : Number(event.target.value))}>
          <option value="">{t('choose')}</option>
          {confidenceChoices(catalogue, method).map((level) => <option key={level} value={String(level)}>{extrapolationConfidenceLabel(level, view.locale)}</option>)}
        </select>
      </label>
      <label className="fa-extrapolation__field">
        <span className="fa-extrapolation__label">{t('factorProfile')}</span>
        <select className="fa-extrapolation__select" value={state.form.profileId ?? ''} data-testid="extrapolation-profile" onChange={(event) => controller.setProfile(event.target.value || null)}>
          <option value="">{t('choose')}</option>
          {catalogue.factor_profiles.map((entry) => <option key={entry.id} value={entry.id}>{entry.label}</option>)}
        </select>
      </label>
    </>
  )
}

/** Aufbau, Zahl der Einheiten aller Zeiträume und Systembewertung (Leitfaden 7.3, 7.8, 7.7). */
function DesignFields({ view }: { view: UseExtrapolation }) {
  const { state, controller, t, method } = view
  const assessments = systemAssessmentChoices(state.catalogue, view.locale)
  return (
    <>
      <label className="fa-extrapolation__field">
        <span className="fa-extrapolation__label">{t('design')}</span>
        <select className="fa-extrapolation__select" value={state.form.design} data-testid="extrapolation-design" onChange={(event) => controller.setDesign(event.target.value as ExtrapolationDesign)}>
          {extrapolationDesignChoices(state.catalogue, t).map((entry) => <option key={entry.id} value={entry.id}>{entry.label}</option>)}
        </select>
        <span className="fa-extrapolation__hint">{t('designHint')}</span>
      </label>
      {state.form.design === 'periods' && method && !method.statistical ? <NumberField view={view} field="populationUnits" label={t('populationUnits')} hint={t('populationUnitsHint')} testId="extrapolation-population-units" /> : null}
      {method?.statistical && assessments.length ? (
        <label className="fa-extrapolation__field">
          <span className="fa-extrapolation__label">{t('systemAssessment')}</span>
          <select className="fa-extrapolation__select" value={state.form.systemAssessment} data-testid="extrapolation-system-assessment" onChange={(event) => controller.setSystemAssessment(event.target.value)}>
            <option value="">{t('systemNone')}</option>
            {assessments.map((entry) => <option key={entry.id} value={entry.id}>{entry.label}</option>)}
          </select>
          <span className="fa-extrapolation__hint">{t('systemAssessmentHint')}</span>
        </label>
      ) : null}
    </>
  )
}

/** Methode, Konfidenzniveau, Faktorprofil, Umfang und Wesentlichkeit (wie `ExtrapolationSettings.vue`). */
export function ExtrapolationSettings({ view }: { view: UseExtrapolation }) {
  const { state, controller, t, method } = view
  const id = useElementId('fa-extrapolation-settings')
  if (!state.catalogue) return null
  const groups = extrapolationMethodGroups(state.catalogue, t)
  return (
    <section className="fa-extrapolation__card" aria-labelledby={`${id}-title`}>
      <h3 id={`${id}-title`} className="fa-extrapolation__heading">{t('settings')}</h3>
      <div className="fa-extrapolation__settings">
        <label className="fa-extrapolation__field">
          <span className="fa-extrapolation__label">{t('method')}</span>
          <select className="fa-extrapolation__select" value={state.form.methodId} data-testid="extrapolation-method" onChange={(event) => controller.selectMethod(event.target.value)}>
            <option value="">{t('choose')}</option>
            {groups.map((group) => (
              <optgroup key={group.label} label={group.label}>
                {group.methods.map((entry) => <option key={entry.id} value={entry.id}>{entry.label}</option>)}
              </optgroup>
            ))}
          </select>
        </label>
        <StatisticalFields view={view} />
        {method?.needs_sample_size ? <NumberField view={view} field="sampleSize" label={t('sampleSize')} hint={t('sampleSizeHint')} testId="extrapolation-sample-size" /> : null}
        <DesignFields view={view} />
        <NumberField view={view} field="materiality" label={`${t('materiality')} (%)`} hint={t('materialityHint')} testId="extrapolation-materiality" />
      </div>
      {method ? (
        <details className="fa-extrapolation__source">
          <summary>{t('methodSource')}</summary>
          <p>{method.source}</p>
          <code>{method.formula}</code>
        </details>
      ) : null}
    </section>
  )
}
