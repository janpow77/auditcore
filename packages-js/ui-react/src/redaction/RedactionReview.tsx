import { redactionReview } from '@auditcore/ui-core'
import { RedactionSide } from './RedactionSide'
import { RedactionViewer } from './RedactionViewer'
import type { UseRedaction } from './useRedaction'

/** Prüfansicht: Seitenbild mit Fundstellen und eigenen Bereichen, Liste der Fundstellen. */
export function RedactionReview({ view: hook, id }: { view: UseRedaction; id: string }) {
  const view = redactionReview(hook.state, hook.t)
  if (!view) return null
  return (
    <section className="fa-redaction__card" aria-labelledby={`${id}-review`} data-testid="redaction-review">
      <h3 id={`${id}-review`} className="fa-redaction__heading">{hook.t('reviewHeading')}</h3>
      <div className="fa-redaction__layout">
        <RedactionViewer hook={hook} view={view} />
        <RedactionSide hook={hook} view={view} />
      </div>
    </section>
  )
}
