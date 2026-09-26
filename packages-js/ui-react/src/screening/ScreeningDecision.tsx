import { useState, type FormEvent } from 'react'
import {
  awaitsSecondReview,
  canDecide,
  requiresFourEyes,
  validateDecision,
  type Outcome,
  type ReviewView,
  type ScreeningTranslate,
  type SettingsView,
  type ViewMessage,
} from '@flowaudit/ui-core'
import { Badge } from '../base/Badge'
import { ScreeningReviewTrail } from './ScreeningReviewTrail'
import { ErrorList, codeKey, useScreeningText } from './shared'

const OUTCOMES: Outcome[] = ['confirmed', 'dismissed', 'deferred']

export interface ScreeningDecisionProps {
  review: ReviewView
  settings: SettingsView | null
  busy: boolean
  hitId: string
  onDecide: (outcome: Outcome, reason: string, fourEyes: boolean) => void
  onSecondReview: (approve: boolean, reason: string) => void
}

function ReasonField({ reason, onReason, t }: { reason: string; onReason: (value: string) => void; t: ScreeningTranslate }) {
  return (
    <label className="fa-screening__field">
      <span>{t('reason')}</span>
      <textarea maxLength={4000} required value={reason} onChange={(event) => onReason(event.target.value)} />
    </label>
  )
}

/** Formularzustand; wird bei neuem Treffer oder neuer Sequenz zurückgesetzt (Schlüssel der Komponente). */
function DecisionForms(props: ScreeningDecisionProps) {
  const { t } = useScreeningText()
  const [outcome, setOutcome] = useState<Outcome | null>(null)
  const [reason, setReason] = useState('')
  const [fourEyes, setFourEyes] = useState(false)
  const [errors, setErrors] = useState<ViewMessage[]>([])
  const policy = outcome !== null && requiresFourEyes(outcome, props.settings)
  const errorTexts = errors.map((error) => t(error.key, error.params))

  function submitDecision(event: FormEvent): void {
    event.preventDefault()
    const found = validateDecision({ outcome, reason, fourEyes })
    setErrors(found)
    if (found.length || outcome === null) return
    props.onDecide(outcome, reason.trim(), fourEyes || policy)
  }

  function submitSecond(approve: boolean): void {
    const found: ViewMessage[] = reason.trim() ? [] : [{ key: 'errorReason' }]
    setErrors(found)
    if (!found.length) props.onSecondReview(approve, reason.trim())
  }

  if (canDecide(props.review)) {
    return (
      <form noValidate onSubmit={submitDecision}>
        <div className="fa-screening__actions" role="group" aria-label={t('decision')}>
          {OUTCOMES.map((o) => (
            <button key={o} type="button" className={`fa-screening__btn fa-screening__btn--${o}`} aria-pressed={outcome === o} title={t(codeKey('hint', o))} onClick={() => setOutcome(o)}>
              {t(codeKey('action', o))}
            </button>
          ))}
        </div>
        {outcome ? <p className="fa-screening__muted">{t(codeKey('hint', outcome))}</p> : null}
        <ReasonField reason={reason} onReason={setReason} t={t} />
        {policy ? <p className="fa-screening__muted">{t('fourEyesPolicy')}</p> : (
          <label className="fa-screening__check">
            <input type="checkbox" checked={fourEyes} onChange={(event) => setFourEyes(event.target.checked)} />{t('fourEyes')}
          </label>
        )}
        <ErrorList texts={errorTexts} />
        <button className="fa-screening__btn fa-screening__btn--primary" type="submit" disabled={props.busy}>{t('saveDecision')}</button>
      </form>
    )
  }
  if (!awaitsSecondReview(props.review)) return <p className="fa-screening__muted">{t('final')}</p>
  return (
    <form noValidate onSubmit={(event) => event.preventDefault()}>
      <p className="fa-screening__muted">{t('secondReviewHint')}</p>
      <ReasonField reason={reason} onReason={setReason} t={t} />
      <ErrorList texts={errorTexts} />
      <div className="fa-screening__actions">
        <button className="fa-screening__btn fa-screening__btn--primary" type="button" disabled={props.busy} onClick={() => submitSecond(true)}>{t('approve')}</button>
        <button className="fa-screening__btn" type="button" disabled={props.busy} onClick={() => submitSecond(false)}>{t('reject')}</button>
      </div>
    </form>
  )
}

/** Entscheidung über einen Treffer bzw. Zweitprüfung nach dem Vier-Augen-Prinzip. */
export function ScreeningDecision(props: ScreeningDecisionProps) {
  const { t } = useScreeningText()
  const { review } = props
  return (
    <section className="fa-screening__panel" aria-labelledby="fa-screening-decision-title">
      <h3 id="fa-screening-decision-title">
        {awaitsSecondReview(review) ? t('secondReview') : t('decision')}
        <Badge tone="accent">{t(codeKey('status', review.status))}</Badge>
      </h3>
      <ScreeningReviewTrail review={review} />
      <DecisionForms key={`${props.hitId}#${review.sequence}`} {...props} />
    </section>
  )
}
