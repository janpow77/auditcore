import { formatScreeningDate as formatDate, type FindingView, type ScreeningTranslate, type SubjectView } from '@flowaudit/ui-core'
import { TitledBadge, useScreeningText } from './shared'

function details(subject: SubjectView, t: ScreeningTranslate): string {
  const input = subject.input
  const parts = [
    input.birth_date ? t('born', { date: input.birth_date }) : '',
    input.country ? t('countryOf', { country: input.country }) : '',
    input.reference ?? '',
    t('normalized', { query: subject.normalized_query }),
  ]
  return parts.filter(Boolean).join(' · ')
}

function findingText(finding: FindingView, t: ScreeningTranslate): string {
  return finding.searched
    ? t('findingSearched', { list: finding.list_name, count: finding.hit_count, date: formatDate(finding.as_of) })
    : t('findingNotSearched', { list: finding.list_name })
}

/** Eingabedaten eines geprüften Namens und Stand je abgefragter Liste. */
export function ScreeningSubjectInfo({ subject }: { subject: SubjectView }) {
  const { t } = useScreeningText()
  return (
    <>
      <div className="fa-screening__muted">{details(subject, t)}</div>
      <div className="fa-screening__findings" role="group" aria-label={t('queriedLists')}>
        {subject.findings.map((finding) => (
          <TitledBadge key={finding.list_key} tone={finding.searched ? 'neutral' : 'danger'} title={finding.note ?? undefined}>
            {findingText(finding, t)}
          </TitledBadge>
        ))}
      </div>
    </>
  )
}
