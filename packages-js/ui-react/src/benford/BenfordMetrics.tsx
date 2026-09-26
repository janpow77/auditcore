import { benfordMetricTexts, levelTone, type BenfordAnalysis, type BenfordTranslate, type ConformityProfile, type Locale } from '@auditcore/ui-core'
import { Badge } from '../base/Badge'

export interface BenfordMetricsProps {
  analysis: BenfordAnalysis
  profile: ConformityProfile | null
  t: BenfordTranslate
  locale: Locale
}

/** Kennzahlen: Anzahl, Ausschlüsse, MAD mit Stufe, Chi², Ziffern über dem kritischen z-Wert (wie `BenfordMetrics.vue`). */
export function BenfordMetrics({ analysis, profile, t, locale }: BenfordMetricsProps) {
  const conformity = analysis.conformity
  const texts = benfordMetricTexts(analysis, profile, t, locale)
  return (
    <dl className="fa-benford__metrics" data-testid="benford-metrics">
      <div className="fa-benford__metric">
        <dt>{t('analysed')}</dt>
        <dd className="fa-benford__value">{texts.analysed}</dd>
      </div>
      <div className="fa-benford__metric">
        <dt>{t('excluded')}</dt>
        <dd className="fa-benford__value">{texts.excluded}</dd>
        <dd className="fa-benford__detail">{texts.excludedDetail}</dd>
      </div>
      <div className="fa-benford__metric">
        <dt>{t('mad')}</dt>
        <dd className="fa-benford__value">{texts.mad}</dd>
        <dd><span className={`fa-badge fa-badge--${levelTone(conformity.mad_level)}`} data-testid="benford-level">{conformity.mad_label}</span></dd>
        <dd className="fa-benford__detail">{texts.madBounds}</dd>
      </div>
      <div className="fa-benford__metric">
        <dt>{t('chi2')}</dt>
        <dd className="fa-benford__value">{texts.chi2}</dd>
        <dd className="fa-benford__detail">{texts.chi2Detail}</dd>
        <dd><Badge tone={conformity.chi2_exceeds ? 'warning' : 'success'}>{texts.chi2Verdict}</Badge></dd>
      </div>
      <div className="fa-benford__metric">
        <dt>{texts.zDigits}</dt>
        <dd className="fa-benford__value" data-testid="benford-exceeding">{texts.exceeding}</dd>
      </div>
    </dl>
  )
}
