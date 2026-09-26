import { benfordValuesText } from '@auditcore/ui-core'
import { TableImport } from '../tabular/TableImport'
import { useElementId } from '../store'
import { BenfordChart } from './BenfordChart'
import { BenfordDigits } from './BenfordDigits'
import { BenfordForm } from './BenfordForm'
import { BenfordMetrics } from './BenfordMetrics'
import { useBenford, type BenfordInputs, type UseBenford } from './useBenford'

export type FlowauditBenfordProps = BenfordInputs

function Result({ view, id, locale }: { view: UseBenford; id: string; locale?: FlowauditBenfordProps['locale'] }) {
  const { state, t, profile } = view
  if (!state.result) return null
  const result = state.result
  return (
    <section className="fa-benford__card" aria-labelledby={`${id}-result`} aria-live="polite">
      <h3 id={`${id}-result`} className="fa-benford__heading">{result.test_label}</h3>
      <p className="fa-benford__notice">{t('notice')}</p>
      <BenfordMetrics analysis={result} profile={profile} t={t} locale={view.locale} />
      <BenfordChart conformity={result.conformity} testLabel={result.test_label} t={t} locale={view.locale} />
      <BenfordDigits conformity={result.conformity} t={t} locale={view.locale} tableLocale={locale} />
    </section>
  )
}

/**
 * Benford-Analyse als native React-Komponente (Vertrag wie `<flowaudit-benford>`):
 * Werte (Eigenschaft oder Datei), Test, Bewertungsprofil, Kennzahlen mit MAD,
 * Chi² und z je Ziffer, SVG-Diagramm und Zifferntabelle. Ereignisse:
 * `onAnalysisCompleted`, `onError`.
 */
export function FlowauditBenford(props: FlowauditBenfordProps) {
  const view = useBenford(props)
  const { state, t, controller } = view
  const id = useElementId('fa-benford')
  return (
    <div className="fa-benford" lang={view.locale}>
      {state.busy === 'load' ? <p className="fa-benford__muted" role="status">{t('loading')}</p> : null}
      {state.error ? <p className="fa-benford__failure" role="alert">{t('failed', { message: state.error })}</p> : null}
      {state.catalogue ? (
        <>
          <div className="fa-benford__inputs">
            <section className="fa-benford__card" aria-labelledby={`${id}-data`}>
              <h3 id={`${id}-data`} className="fa-benford__heading">{t('data')}</h3>
              <p className="fa-benford__muted" data-testid="benford-count">{benfordValuesText(view.values.length, t, view.locale)}</p>
              <TableImport mode="values" locale={props.locale} onImport={(columns) => controller.useValues(columns.values)} />
            </section>
            <BenfordForm view={view} id={id} />
          </div>
          <Result view={view} id={id} locale={props.locale} />
        </>
      ) : null}
    </div>
  )
}
