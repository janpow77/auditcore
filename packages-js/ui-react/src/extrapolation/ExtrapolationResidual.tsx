import { extrapolationIssueText, RESIDUAL_FIELDS, residualColumns, residualMetrics, residualRows, type Locale } from '@auditcore/ui-core'
import { Button } from '../base/Button'
import { useElementId } from '../store'
import { FlowauditTable } from '../table/FlowauditTable'
import { MetricList } from './ExtrapolationResult'
import type { UseExtrapolation } from './useExtrapolation'

/** Restfehlerquote nach Finanzkorrekturen, getrennt von der TER (wie `ExtrapolationResidual.vue`). */
export function ExtrapolationResidual({ view, tableLocale }: { view: UseExtrapolation; tableLocale?: Locale }) {
  const { state, controller, t, locale } = view
  const id = useElementId('fa-extrapolation-residual')
  const rer = state.residual?.residual_error_rate ?? null
  return (
    <section className="fa-extrapolation__card fa-extrapolation__card--residual" aria-labelledby={`${id}-title`}>
      <h3 id={`${id}-title`} className="fa-extrapolation__heading">{t('residualTitle')}</h3>
      <p className="fa-extrapolation__hint">{t('residualNotice')}</p>
      <div className="fa-extrapolation__settings">
        {RESIDUAL_FIELDS.map((field) => {
          const issue = extrapolationIssueText(state.residualIssues, field.key, t)
          return (
            <label key={field.key} className="fa-extrapolation__field">
              <span className="fa-extrapolation__label">{`${t(field.label)}${field.key === 'terRate' ? ' (%)' : ''}`}</span>
              <input
                className="fa-extrapolation__input fa-extrapolation__input--number"
                inputMode="decimal"
                value={state.residualForm[field.key]}
                aria-invalid={issue ? 'true' : undefined}
                data-testid={`extrapolation-rer-${field.key}`}
                onChange={(event) => controller.setResidual({ [field.key]: event.target.value })}
              />
              {issue ? <span className="fa-extrapolation__error">{issue}</span> : null}
            </label>
          )
        })}
      </div>
      <div className="fa-extrapolation__actions">
        <Button variant="primary" loading={state.busy === 'residual'} testId="extrapolation-residual" onClick={() => void controller.computeResidual()}>{t('computeResidual')}</Button>
      </div>
      {rer ? (
        <>
          <MetricList metrics={residualMetrics(rer, t, locale)} testId="extrapolation-rer" />
          <FlowauditTable columns={residualColumns(t, locale)} rows={residualRows(rer)} caption={t('residualTitle')} locale={tableLocale} testId="extrapolation-rer-rows" />
        </>
      ) : null}
    </section>
  )
}
