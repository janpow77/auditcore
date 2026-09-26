import { saveFile } from '@flowaudit/common/browser'
import { extrapolationFormMessage, type ExtrapolationExportFormat } from '@flowaudit/ui-core'
import { Button } from '../base/Button'
import { ExtrapolationResidual } from './ExtrapolationResidual'
import { ExtrapolationResult } from './ExtrapolationResult'
import { ExtrapolationSettings } from './ExtrapolationSettings'
import { ExtrapolationStrata } from './ExtrapolationStrata'
import { ExtrapolationUnits } from './ExtrapolationUnits'
import { useExtrapolation, type ExtrapolationInputs, type UseExtrapolation } from './useExtrapolation'

export type FlowauditExtrapolationProps = ExtrapolationInputs

function Results({ view, locale }: { view: UseExtrapolation; locale?: FlowauditExtrapolationProps['locale'] }) {
  const { state, controller, t } = view
  if (!state.result) return null
  const onExport = async (format: ExtrapolationExportFormat): Promise<void> => {
    const file = await controller.exportEvaluation(format)
    if (file) saveFile(file)
  }
  return (
    <>
      <ExtrapolationResult result={state.result} catalogue={state.catalogue} busy={state.busy === 'export'} t={t} locale={view.locale} tableLocale={locale} onExport={(format) => void onExport(format)} />
      <ExtrapolationResidual view={view} tableLocale={locale} />
    </>
  )
}

/**
 * Hochrechnung von Stichprobenfehlern als native React-Komponente (Vertrag wie
 * `<flowaudit-extrapolation>`): Methode und Konfidenzniveau, Schichten und
 * geprüfte Einheiten mit zufälligen, systemischen und anomalen Fehlern,
 * Gesamtfehlerquote (TER) mit Fehlerobergrenze und Herleitung, Export und
 * getrennt davon die Restfehlerquote (RER). Ereignisse:
 * `onEvaluationCompleted`, `onResidualComputed`, `onError`.
 */
export function FlowauditExtrapolation(props: FlowauditExtrapolationProps) {
  const view = useExtrapolation(props)
  const { state, t, controller } = view
  const message = extrapolationFormMessage(state.formError, state.issues, t)
  return (
    <div className="fa-extrapolation" lang={view.locale}>
      {state.busy === 'load' ? <p className="fa-extrapolation__muted" role="status">{t('loading')}</p> : null}
      {state.error ? <p className="fa-extrapolation__failure" role="alert">{t('failed', { message: state.error })}</p> : null}
      {state.catalogue ? (
        <>
          <ExtrapolationSettings view={view} />
          <ExtrapolationStrata view={view} />
          <ExtrapolationUnits view={view} />
          <div className="fa-extrapolation__actions">
            <Button variant="primary" loading={state.busy === 'evaluate'} testId="extrapolation-evaluate" onClick={() => void controller.evaluate()}>{t('evaluate')}</Button>
            {message ? <p className="fa-extrapolation__error" role="alert" data-testid="extrapolation-form-error">{message}</p> : null}
          </div>
          <Results view={view} locale={props.locale} />
        </>
      ) : null}
    </div>
  )
}
