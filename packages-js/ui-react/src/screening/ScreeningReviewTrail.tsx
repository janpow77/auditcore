import { formatScreeningDate as formatDate, type ReviewView, type ScreeningTranslate } from '@auditcore/ui-core'
import { codeKey, useScreeningText } from './shared'

function decisionLine(review: ReviewView, t: ScreeningTranslate): string {
  const entry = review.decision
  if (!entry) return ''
  const line = t('lastDecision', { outcome: t(codeKey('status', entry.outcome)), actor: entry.actor.display_name, date: formatDate(entry.at) })
  const marker = entry.four_eyes ? ` ${t(entry.four_eyes_source === 'policy' ? 'fourEyesMarkerPolicy' : 'fourEyesMarker')}` : ''
  return `${line}${marker} – „${entry.reason}“`
}

function secondLine(review: ReviewView, t: ScreeningTranslate): string {
  const entry = review.second_review
  if (!entry) return ''
  const result = t(entry.approve ? 'approved' : 'rejected')
  return `${t('secondReviewDone', { result, actor: entry.actor.display_name, date: formatDate(entry.at) })} – „${entry.reason}“`
}

/** Letzte Entscheidung und Zweitprüfung eines Treffers. */
export function ScreeningReviewTrail({ review }: { review: ReviewView }) {
  const { t } = useScreeningText()
  const decision = decisionLine(review, t)
  const second = secondLine(review, t)
  return (
    <>
      {decision ? <div className="fa-screening__muted">{decision}</div> : null}
      {second ? <div className="fa-screening__muted">{second}</div> : null}
    </>
  )
}
