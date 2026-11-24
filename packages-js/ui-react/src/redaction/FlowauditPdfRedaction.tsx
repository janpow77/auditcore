import { useEffect, useRef } from 'react'
import { focusRedactionHeading, redactionStep } from '@auditcore/ui-core'
import { useElementId } from '../store'
import { RedactionForm } from './RedactionForm'
import { RedactionResultView } from './RedactionResult'
import { RedactionReview } from './RedactionReview'
import { useRedaction, type RedactionInputs } from './useRedaction'

export type FlowauditPdfRedactionProps = RedactionInputs

/**
 * „PDF schwärzen“ als native React-Komponente (Vertrag wie `<flowaudit-pdf-redaction>`):
 * Suchkriterien, Prüfansicht mit Seitenbild und eigenen Bereichen, nachgeprüftes
 * Ergebnis zum Herunterladen. Ereignisse: `onRedactionPlanned`,
 * `onRedactionCompleted`, `onError`.
 */
export function FlowauditPdfRedaction(props: FlowauditPdfRedactionProps) {
  const view = useRedaction(props)
  const { state, t } = view
  const id = useElementId('fa-redaction')
  const step = redactionStep(state)
  const root = useRef<HTMLDivElement | null>(null)
  const shown = useRef(step)
  // Schrittwechsel: Fokus auf die neue Überschrift, damit er nicht auf <body> fällt.
  useEffect(() => {
    if (shown.current === step) return
    shown.current = step
    focusRedactionHeading(root.current)
  }, [step])
  return (
    <div ref={root} className="fa-redaction" lang={view.locale} data-testid="redaction">
      {!props.port ? <p className="fa-redaction__muted">{t('noPort')}</p> : null}
      {state.busy === 'load' ? <p className="fa-redaction__muted" role="status">{t('loading')}</p> : null}
      {state.error ? <p className="fa-redaction__failure" role="alert">{t('failed', { message: state.error })}</p> : null}
      {state.catalogue && step === 'form' ? <RedactionForm view={view} id={id} /> : null}
      {step === 'review' ? <RedactionReview view={view} id={id} /> : null}
      {step === 'result' ? <RedactionResultView view={view} id={id} /> : null}
    </div>
  )
}
