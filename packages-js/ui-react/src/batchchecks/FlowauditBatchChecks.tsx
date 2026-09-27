import { useElementId } from '../store'
import { BatchChecksInput } from './BatchChecksInput'
import { BatchChecksResult } from './BatchChecksResult'
import { useBatchChecks, type BatchChecksInputs } from './useBatchChecks'

export type FlowauditBatchChecksProps = BatchChecksInputs

/**
 * Bestandsprüfung als native React-Komponente (Vertrag wie `<flowaudit-batch-checks>`):
 * Bestand als CSV oder JSON einlesen, Spalten zuordnen, Prüflauf mit Befunden je
 * Regel und betroffenen Belegen, Export. Ereignisse: `onChecksCompleted`, `onError`.
 */
export function FlowauditBatchChecks(props: FlowauditBatchChecksProps) {
  const view = useBatchChecks(props)
  const { state, t } = view
  const id = useElementId('fa-batchchecks')
  return (
    <section className="fa-batchchecks" lang={view.locale} aria-label={t('title')} data-testid="batchchecks">
      {!props.port ? <p className="fa-batchchecks__muted">{t('noPort')}</p> : null}
      {state.busy === 'load' ? <p className="fa-batchchecks__muted" role="status">{t('loading')}</p> : null}
      {state.error ? <p className="fa-batchchecks__failure" role="alert">{t('failed', { message: state.error })}</p> : null}
      {state.catalogue ? <BatchChecksInput view={view} id={id} /> : null}
      {state.answer ? <BatchChecksResult view={view} answer={state.answer} id={id} /> : null}
    </section>
  )
}
