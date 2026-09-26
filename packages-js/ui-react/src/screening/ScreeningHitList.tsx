import { codeLabel, formatScore, scorePercent, type BadgeTone, type HitView, type ReviewStatus, type SubjectStatus, type SubjectView } from '@auditcore/ui-core'
import { Badge } from '../base/Badge'
import { codeKey, useScreeningText } from './shared'
import { ScreeningSubjectInfo } from './ScreeningSubjectInfo'

const STATUS_TONE: Record<ReviewStatus, BadgeTone> = { open: 'warning', pending_second_review: 'warning', deferred: 'neutral', confirmed: 'danger', dismissed: 'success' }
const SUBJECT_TONE: Record<SubjectStatus, BadgeTone> = { HITS: 'warning', NO_HITS: 'success', INCOMPLETE: 'danger', NOT_SEARCHED: 'danger' }

export interface ScreeningHitListProps {
  subjects: readonly SubjectView[]
  selectedId: string | null
  onSelect: (hitId: string) => void
}

function HitButton({ hit, selected, onSelect }: { hit: HitView; selected: boolean; onSelect: (hitId: string) => void }) {
  const { t, locale } = useScreeningText()
  const scale = hit.breakdown.scale
  return (
    <button type="button" className="fa-screening__hit" aria-current={selected} onClick={() => onSelect(hit.hit_id)}>
      <span className="fa-screening__hit-name">{hit.entry.name}</span>
      <span className="fa-screening__bar" aria-hidden="true">
        <span style={{ width: `${scorePercent(hit.score, scale)}%` }} />
        <i style={{ left: `${scorePercent(hit.breakdown.min_score, scale)}%` }} />
      </span>
      <span className="fa-screening__score">{formatScore(hit.score, scale, locale)}</span>
      <span className="fa-screening__hit-meta">
        <span>{hit.list_name}</span>
        <span>· {codeLabel(t, 'class', hit.confidence)}</span>
        {hit.matched_field === 'alias' ? <span>· {t('viaAlias', { name: hit.matched_name })}</span> : null}
        {hit.dob_conflict ? <Badge tone="danger">{t('dobConflict')}</Badge> : null}
        {hit.country_conflict ? <Badge tone="danger">{t('countryConflict')}</Badge> : null}
        <Badge tone={STATUS_TONE[hit.review.status]}>{t(codeKey('status', hit.review.status))}</Badge>
      </span>
    </button>
  )
}

function Subject({ subject, selectedId, onSelect }: { subject: SubjectView } & Omit<ScreeningHitListProps, 'subjects'>) {
  const { t } = useScreeningText()
  return (
    <article className="fa-screening__subject">
      <header className="fa-screening__subject-head">
        <strong>{subject.input.name}</strong>
        <Badge tone={SUBJECT_TONE[subject.status]}>{t(codeKey('subject', subject.status))}</Badge>
      </header>
      <ScreeningSubjectInfo subject={subject} />
      {subject.hits.length ? null : <p className="fa-screening__empty">{subject.hits_before_filter ? t('noHitsFiltered') : t('noHits')}</p>}
      <ul className="fa-screening__hits">
        {subject.hits.map((hit) => (
          <li key={hit.hit_id}><HitButton hit={hit} selected={hit.hit_id === selectedId} onSelect={onSelect} /></li>
        ))}
      </ul>
      {subject.truncated ? <p className="fa-screening__muted">{t('truncated', { total: subject.total_hits })}</p> : null}
      {subject.limitations.length ? (
        <details className="fa-screening__muted">
          <summary>{t('limitations')}</summary>
          <ul>{subject.limitations.map((text) => <li key={text}>{text}</li>)}</ul>
        </details>
      ) : null}
    </article>
  )
}

/** Treffer je geprüftem Namen mit Score-Balken, Liste, Stufe und Prüfstatus. */
export function ScreeningHitList({ subjects, selectedId, onSelect }: ScreeningHitListProps) {
  const { t } = useScreeningText()
  return (
    <section className="fa-screening__panel" aria-labelledby="fa-screening-hits-title">
      <h3 id="fa-screening-hits-title">{t('hits')}</h3>
      {subjects.map((subject) => <Subject key={subject.subject_id} subject={subject} selectedId={selectedId} onSelect={onSelect} />)}
    </section>
  )
}
