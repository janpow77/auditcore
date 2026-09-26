import { filterOptions, formatScreeningDate as formatDate, type HitFilter, type HitView, type LogEntry, type Outcome, type ReviewStatus, type RunView, type SettingsView, type SubjectView } from '@flowaudit/ui-core'
import { ScreeningComparison } from './ScreeningComparison'
import { ScreeningDecision } from './ScreeningDecision'
import { ScreeningFilters } from './ScreeningFilters'
import { ScreeningHitList } from './ScreeningHitList'
import { ScreeningLog } from './ScreeningLog'
import { ScreeningScoreBreakdown } from './ScreeningScoreBreakdown'
import { ScreeningSources } from './ScreeningSources'
import { codeKey, useScreeningText } from './shared'

export interface ScreeningRunDetailProps {
  run: RunView
  subjects: readonly SubjectView[]
  selected: { subject: SubjectView; hit: HitView } | null
  filter: HitFilter
  settings: SettingsView | null
  events: readonly LogEntry[]
  busy: boolean
  onFilterChange: (value: HitFilter) => void
  onSelect: (hitId: string) => void
  onNext: () => void
  onDecide: (outcome: Outcome, reason: string, fourEyes: boolean) => void
  onSecondReview: (approve: boolean, reason: string) => void
}

function RunHead({ run }: { run: RunView }) {
  const { t } = useScreeningText()
  const counts = Object.entries(run.review_counts) as [ReviewStatus, number][]
  return (
    <section className="fa-screening__panel" aria-labelledby="fa-screening-run-title">
      <h3 id="fa-screening-run-title">
        {run.case_reference || t('run')}
        <span className="fa-screening__muted">{formatDate(run.created_at)} · {run.created_by.display_name}</span>
      </h3>
      <div className="fa-screening__summary">
        <span>{t(codeKey('kind', run.kind))}</span>
        <span>{t('profileLine', { id: run.profile.id, version: run.profile.version })}</span>
        <span>{t('namesHits', { names: run.subject_count, hits: run.hit_count })}</span>
        {counts.map(([status, count]) => <span key={status}>{t(codeKey('status', status))}: {count}</span>)}
      </div>
      {run.subjects_incomplete ? <p className="fa-screening__alert" role="status">{t('incompleteRun', { count: run.subjects_incomplete })}</p> : null}
    </section>
  )
}

/** Geöffneter Prüflauf: Kopf, Filter, Treffer, Vergleich, Aufschlüsselung, Entscheidung, Protokoll, Quellenstand. */
export function ScreeningRunDetail(props: ScreeningRunDetailProps) {
  const { t } = useScreeningText()
  const { run, selected } = props
  return (
    <>
      <RunHead run={run} />
      <ScreeningFilters value={props.filter} options={filterOptions(run)} onChange={props.onFilterChange} />
      <div className="fa-screening__main">
        <ScreeningHitList subjects={props.subjects} selectedId={selected?.hit.hit_id ?? null} onSelect={props.onSelect} />
        {selected ? (
          <div>
            <ScreeningComparison subject={selected.subject} hit={selected.hit} />
            <ScreeningScoreBreakdown breakdown={selected.hit.breakdown} />
            <ScreeningDecision
              review={selected.hit.review}
              hitId={selected.hit.hit_id}
              settings={props.settings}
              busy={props.busy}
              onDecide={props.onDecide}
              onSecondReview={props.onSecondReview}
            />
            <button type="button" className="fa-screening__btn" data-testid="screening-next" onClick={props.onNext}>{t('nextOpen')}</button>
          </div>
        ) : <p className="fa-screening__panel fa-screening__empty">{t('noSelection')}</p>}
      </div>
      <ScreeningLog events={props.events} />
      <ScreeningSources sources={run.sources} title={t('sourcesOfRun')} />
    </>
  )
}
