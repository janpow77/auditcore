import { Fragment } from 'react'
import { formatValue, pairs, recordLabel, riskMessages, type FlagEntry, type Locale, type ProfileReference, type RecordView } from '@auditcore/ui-core'
import { useTranslation } from '../i18n'
import { RiskFlagCard } from './RiskFlagCard'

export interface RiskRecordDetailProps {
  record?: RecordView | null
  entries?: readonly FlagEntry[]
  profile?: ProfileReference | null
  locale?: Locale
}

/** Detailansicht eines Datensatzes (Karten je Treffer/unbestimmtem Merkmal, Bewertung), wie `RiskRecordDetail`. */
export function RiskRecordDetail({ record = null, entries = [], profile = null, locale }: RiskRecordDetailProps) {
  const { t, locale: active } = useTranslation(riskMessages, locale)
  const assessment = pairs(record?.assessment).filter(([, value]) => typeof value !== 'object' || value === null)
  return (
    <section className="fa-risk-detail" aria-live="polite" data-testid="risk-detail">
      {!record ? <p className="fa-risk-detail__empty">{t('detailEmpty')}</p> : (
        <>
          <h3>{t('detailTitle', { record: recordLabel(record) })}</h3>
          {entries.length === 0 ? <p className="fa-risk-detail__empty">{t('detailNone')}</p> : null}
          {entries.map((entry) => <RiskFlagCard key={entry.code} entry={entry} profile={profile} locale={locale} />)}
          {assessment.length ? (
            <dl className="fa-risk-detail__assessment" aria-label={t('assessment')}>
              {assessment.map(([name, value]) => (
                <Fragment key={name}>
                  <dt>{name}</dt>
                  <dd>{formatValue(value, active, t('emptyValue'))}</dd>
                </Fragment>
              ))}
            </dl>
          ) : null}
        </>
      )}
    </section>
  )
}
