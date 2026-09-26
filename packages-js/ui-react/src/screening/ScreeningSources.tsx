import { intlFormatNumber } from '@auditcore/common'
import { formatAge, formatScreeningDate as formatDate, freshnessTone, type BadgeTone, type FreshnessStatus, type ScreeningTranslate, type SourceView } from '@auditcore/ui-core'
import { Badge } from '../base/Badge'
import { TitledBadge, codeKey, useScreeningText } from './shared'

const TONES: Record<'ok' | 'warn' | 'muted', BadgeTone> = { ok: 'success', warn: 'warning', muted: 'neutral' }
const tone = (status: FreshnessStatus): BadgeTone => TONES[freshnessTone(status)]

export interface ScreeningSourcesProps {
  sources: readonly SourceView[]
  checkedAt?: string | null
  title?: string
  compact?: boolean
}

function CompactList({ sources, t, count }: { sources: readonly SourceView[]; t: ScreeningTranslate; count: (value: number) => string }) {
  return (
    <ul className="fa-screening__source-list">
      {sources.map((source) => (
        <li key={source.list.key}>
          <strong>{source.list.name}</strong>
          <span>
            <Badge tone={tone(source.freshness.status)}>{t(codeKey('fresh', source.freshness.status))}</Badge>
            {source.searchable ? null : <Badge tone="danger">{t('noStock')}</Badge>}
          </span>
          <span className="fa-screening__muted">
            {t('asOf', { date: source.as_of ? formatDate(source.as_of) : t('unknown') })} · {formatAge(source.freshness.age_days, t)} · {t('entries', { count: count(source.entry_count) })}
          </span>
        </li>
      ))}
    </ul>
  )
}

function SourceRow({ source, t, count }: { source: SourceView; t: ScreeningTranslate; count: (value: number) => string }) {
  const list = source.list
  return (
    <tr>
      <td>
        {list.url ? <a href={list.url} target="_blank" rel="noopener noreferrer">{list.name}</a> : <span>{list.name}</span>}
        <div className="fa-screening__muted">{t('via', { kind: t(codeKey('kind', source.kind)), issuer: list.issuer, provider: list.provider })}</div>
        {list.data_licence.status ? (
          <div className="fa-screening__muted" title={list.data_licence.note}>{t('dataLicence', { status: list.data_licence.status })}</div>
        ) : null}
      </td>
      <td>
        {source.searchable ? <span>{count(source.entry_count)}</span> : <TitledBadge tone="danger" title={t('noStockHint')}>{t('noStock')}</TitledBadge>}
      </td>
      <td>
        <div>{source.as_of ? formatDate(source.as_of) : '–'}</div>
        <Badge tone={tone(source.freshness.status)}>{t(codeKey('fresh', source.freshness.status))}</Badge>
        <div className="fa-screening__muted">{formatAge(source.freshness.age_days, t)}</div>
      </td>
    </tr>
  )
}

/** Quellenstand: kompakt (Seitenleiste) oder als Tabelle zum Zeitpunkt des Prüflaufs. */
export function ScreeningSources({ sources, checkedAt, title, compact }: ScreeningSourcesProps) {
  const { t, locale } = useScreeningText()
  const headingId = compact ? 'fa-screening-sources-now' : 'fa-screening-sources-run'
  const count = (value: number): string => intlFormatNumber(value, locale)
  return (
    <section className="fa-screening__panel" aria-labelledby={headingId}>
      <h3 id={headingId}>
        {title ?? t('sources')}
        {checkedAt ? <span className="fa-screening__muted">{t('checkedAt', { date: formatDate(checkedAt) })}</span> : null}
      </h3>
      {!sources.length ? <p className="fa-screening__empty">{t('noSources')}</p> : compact ? <CompactList sources={sources} t={t} count={count} /> : (
        <table className="fa-screening__table">
          <thead>
            <tr>
              <th scope="col">{t('columnList')}</th>
              <th scope="col">{t('columnEntries')}</th>
              <th scope="col">{t('columnAsOf')}</th>
            </tr>
          </thead>
          <tbody>
            {sources.map((source) => <SourceRow key={source.list.key} source={source} t={t} count={count} />)}
          </tbody>
        </table>
      )}
    </section>
  )
}
