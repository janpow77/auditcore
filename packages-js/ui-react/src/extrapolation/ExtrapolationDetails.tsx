import {
  detailWarnings,
  groupColumns,
  groupRows,
  periodColumns,
  periodRows,
  recalculationView,
  subsampleColumns,
  subsampleResultRows,
  type EvaluationResult,
  type ExtrapolationCatalogue,
  type ExtrapolationTranslate,
  type Locale,
} from '@auditcore/ui-core'
import { useElementId } from '../store'
import { FlowauditTable } from '../table/FlowauditTable'

export interface ExtrapolationDetailsProps {
  result: EvaluationResult
  catalogue: ExtrapolationCatalogue | null
  t: ExtrapolationTranslate
  locale: Locale
  tableLocale?: Locale
}

/** Zeiträume, Programme, Teilstichproben und Neuberechnung des Konfidenzniveaus (wie `ExtrapolationDetails.vue`). */
export function ExtrapolationDetails({ result, catalogue, t, locale, tableLocale }: ExtrapolationDetailsProps) {
  const id = useElementId('fa-extrapolation-details')
  const periods = periodRows(result)
  const groups = groupRows(result, catalogue)
  const subsamples = subsampleResultRows(result, t)
  const recalculation = recalculationView(result, t, locale)
  const warnings = detailWarnings(result)
  const title = result.design === 'groups' ? t('detailsGroups') : result.design === 'periods' ? t('detailsPeriods') : t('recalcTitle')
  return (
    <section className="fa-extrapolation__card" aria-labelledby={`${id}-title`} data-testid="extrapolation-details">
      <h3 id={`${id}-title`} className="fa-extrapolation__heading">{title}</h3>
      {periods.length ? <FlowauditTable columns={periodColumns(t, locale)} rows={periods} caption={t('detailsPeriods')} locale={tableLocale} testId="extrapolation-periods" /> : null}
      {groups.length ? <FlowauditTable columns={groupColumns(t, locale)} rows={groups} caption={t('detailsGroups')} locale={tableLocale} testId="extrapolation-groups" /> : null}
      {subsamples.length ? <FlowauditTable columns={subsampleColumns(t, locale)} rows={subsamples} caption={t('detailsSubsamples')} locale={tableLocale} testId="extrapolation-subsamples" /> : null}
      {recalculation ? (
        <>
          <h4 className="fa-extrapolation__heading">{t('recalcTitle')}</h4>
          <dl className="fa-extrapolation__metrics" data-testid="extrapolation-recalculation">
            {recalculation.metrics.map((metric) => (
              <div key={metric.id} className="fa-extrapolation__metric" data-metric={metric.id}>
                <dt>{metric.label}</dt>
                <dd className="fa-extrapolation__value">{metric.value}</dd>
              </div>
            ))}
          </dl>
          <p className="fa-extrapolation__hint">{recalculation.verdict}</p>
        </>
      ) : null}
      {warnings.length ? (
        <ul className="fa-extrapolation__warnings">
          {warnings.map((line) => <li key={line}>{line}</li>)}
        </ul>
      ) : null}
    </section>
  )
}
