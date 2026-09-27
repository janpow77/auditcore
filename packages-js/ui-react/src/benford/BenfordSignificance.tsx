import { benfordChiTexts, benfordDigitZTexts, type BenfordAnalysis, type BenfordTranslate, type Locale } from '@auditcore/ui-core'
import { Badge } from '../base/Badge'

export interface BenfordSignificanceProps {
  metrics: NonNullable<BenfordAnalysis['metrics']>
  t: BenfordTranslate
  locale: Locale
}

/** Zusätzliche Kennzahlen: Chi²-Test mit kritischen Werten, auffällige Ziffern (wie `BenfordSignificance.vue`). */
export function BenfordSignificance({ metrics, t, locale }: BenfordSignificanceProps) {
  const chi = metrics.chi_square ? benfordChiTexts(metrics.chi_square, t, locale) : null
  const z = metrics.digit_z ? benfordDigitZTexts(metrics.digit_z, t, locale) : null
  return (
    <dl className="fa-benford__metrics" data-testid="benford-significance" aria-label={t('significance')}>
      {chi ? (
        <div className="fa-benford__metric">
          <dt>{t('chiTest')}</dt>
          <dd className="fa-benford__value">{chi.statistic}</dd>
          <dd className="fa-benford__detail">{chi.detail}</dd>
          <dd className="fa-benford__detail" data-testid="benford-critical">{chi.critical}</dd>
          <dd><Badge tone={chi.tone}>{chi.verdict}</Badge></dd>
        </div>
      ) : null}
      {z ? (
        <div className="fa-benford__metric">
          <dt>{t('digitZ')}</dt>
          <dd className="fa-benford__value" data-testid="benford-conspicuous">{z.digits}</dd>
          <dd className="fa-benford__detail">{z.detail}</dd>
          <dd className="fa-benford__detail">{z.largest}</dd>
        </div>
      ) : null}
    </dl>
  )
}
