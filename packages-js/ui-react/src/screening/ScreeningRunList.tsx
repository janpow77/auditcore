import { formatScreeningDate as formatDate, type RunSummary, type ScreeningTranslate } from '@flowaudit/ui-core'
import { Badge } from '../base/Badge'
import { codeKey, useScreeningText } from './shared'

const openCount = (run: RunSummary): number => run.review_counts.open + run.review_counts.deferred + run.review_counts.pending_second_review

function summary(run: RunSummary, t: ScreeningTranslate): string {
  return t('runSummary', {
    kind: t(codeKey('kind', run.kind)),
    names: run.subject_count,
    hits: run.hit_count,
    date: formatDate(run.created_at),
    actor: run.created_by.display_name,
  })
}

/** Liste der Prüfläufe; ein Klick öffnet den Lauf. */
export function ScreeningRunList({ runs, activeId, onOpen }: { runs: readonly RunSummary[]; activeId: string | null; onOpen: (runId: string) => void }) {
  const { t } = useScreeningText()
  return (
    <section className="fa-screening__panel" aria-labelledby="fa-screening-runs-title">
      <h3 id="fa-screening-runs-title">{t('runs')}</h3>
      {!runs.length ? <p className="fa-screening__empty">{t('noRuns')}</p> : (
        <ul className="fa-screening__runs">
          {runs.map((run) => (
            <li key={run.run_id}>
              <button type="button" aria-current={run.run_id === activeId} onClick={() => onOpen(run.run_id)}>
                <strong>{run.case_reference || t('runDated', { date: formatDate(run.created_at) })}</strong>
                <span className="fa-screening__muted">{summary(run, t)}</span>
                <span>
                  {run.review_complete ? <Badge tone="success">{t('complete')}</Badge> : <Badge tone="warning">{t('openCount', { count: openCount(run) })}</Badge>}
                  {run.subjects_incomplete ? <Badge tone="danger">{t('incompleteCount', { count: run.subjects_incomplete })}</Badge> : null}
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
