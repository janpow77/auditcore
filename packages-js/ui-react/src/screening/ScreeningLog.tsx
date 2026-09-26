import { formatScreeningDate as formatDate, type LogEntry, type ScreeningTranslate } from '@auditcore/ui-core'
import { useScreeningText } from './shared'

function reasonOf(entry: LogEntry): string | null {
  const reason = entry.data['reason']
  return typeof reason === 'string' ? reason : null
}

function detail(entry: LogEntry, t: ScreeningTranslate): string {
  if (entry.type === 'second_review_recorded') {
    const result = t(entry.data['approve'] === true ? 'approved' : 'rejected')
    return t('logSecondReview', { result, outcome: entry.outcome_label ?? '–' })
  }
  if (entry.type === 'decision_recorded') {
    return `${entry.outcome_label ?? ''}${entry.data['four_eyes'] === true ? t('logFourEyes') : ''}`
  }
  const count = entry.data['subjects']
  return typeof count === 'number' ? t('logSubjects', { count }) : ''
}

/** Protokoll des Prüflaufs (Anlage, Entscheidungen, Zweitprüfungen). */
export function ScreeningLog({ events }: { events: readonly LogEntry[] }) {
  const { t } = useScreeningText()
  return (
    <section className="fa-screening__panel" aria-labelledby="fa-screening-log-title">
      <h3 id="fa-screening-log-title">{t('log')}</h3>
      {events.length ? null : <p className="fa-screening__empty">{t('logEmpty')}</p>}
      <ol className="fa-screening__log">
        {events.map((entry) => {
          const reason = reasonOf(entry)
          return (
            <li key={entry.sequence} className={`fa-screening__log--${entry.type}`}>
              <strong>#{entry.sequence} {entry.type_label}</strong> – {detail(entry, t)}
              <div className="fa-screening__muted">
                {formatDate(entry.at)} · {entry.actor.display_name}
                {entry.hit ? <span> · {entry.hit.subject_name} ↔ {entry.hit.entry_name} ({entry.hit.list_name})</span> : null}
              </div>
              {reason ? <div>„{reason}“</div> : null}
            </li>
          )
        })}
      </ol>
    </section>
  )
}
