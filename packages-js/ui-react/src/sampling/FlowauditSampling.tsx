import { saveFile } from '@auditcore/common/browser'
import { isStratifiedPopulation, type ExportFormat } from '@auditcore/ui-core'
import { SamplingDraw } from './SamplingDraw'
import { SamplingMethod } from './SamplingMethod'
import { SamplingParameters } from './SamplingParameters'
import { SamplingPopulation } from './SamplingPopulation'
import { SamplingResult } from './SamplingResult'
import { SamplingSelectionResult } from './SamplingSelectionResult'
import { useSampling, type SamplingInputs, type UseSampling } from './useSampling'

export type FlowauditSamplingProps = SamplingInputs

function Sizing({ view, locale }: { view: UseSampling; locale?: FlowauditSamplingProps['locale'] }) {
  const { state, profile, controller, t } = view
  if (!state.catalogue) return null
  return (
    <div className="fa-sampling__grid">
      <SamplingMethod catalogue={state.catalogue} profile={profile} methodId={state.methodId} t={t} onMethodChange={controller.selectMethod} />
      {profile ? (
        <SamplingParameters
          profile={profile}
          errors={state.fieldErrors}
          texts={state.texts}
          confidence={state.confidence}
          busy={state.busy === 'size'}
          hasPopulation={view.population.length > 0}
          t={t}
          locale={view.locale}
          onTextsChange={controller.setTexts}
          onConfidenceChange={controller.setConfidence}
          onCalculate={() => void controller.calculate()}
          onSuggest={controller.applySuggestions}
        />
      ) : null}
      {state.size ? <SamplingResult result={state.size} t={t} locale={view.locale} tableLocale={locale} /> : null}
    </div>
  )
}

function Selection({ view, locale }: { view: UseSampling; locale?: FlowauditSamplingProps['locale'] }) {
  const { state, profile, controller, t } = view
  if (!state.catalogue || !profile) return null
  const onExport = async (format: ExportFormat): Promise<void> => {
    const file = await controller.exportSelection(format)
    if (file) saveFile(file)
  }
  return (
    <section className="fa-sampling__card">
      <SamplingDraw
        profile={profile}
        variants={state.catalogue.selection_variants}
        allocations={state.catalogue.allocation_methods}
        stratified={isStratifiedPopulation(view.population)}
        error={state.selectionError}
        busy={state.busy === 'selection'}
        canRedraw={state.selection !== null}
        sampleSize={state.sampleSize}
        seed={state.seed}
        variant={state.variant}
        allocation={state.allocation}
        t={t}
        onSampleSizeChange={controller.setSampleSize}
        onSeedChange={controller.setSeed}
        onVariantChange={controller.setVariant}
        onAllocationChange={controller.setAllocation}
        onDraw={(fresh) => void controller.draw(fresh)}
      />
      {state.selection ? <SamplingSelectionResult result={state.selection} busy={state.busy === 'export'} t={t} locale={view.locale} tableLocale={locale} onExport={(format) => void onExport(format)} /> : null}
    </section>
  )
}

/**
 * Stichprobenrechner als native React-Komponente (Vertrag wie `<flowaudit-sampling>`):
 * Methodenprofil, Stichprobenumfang mit Herleitung, Grundgesamtheit (Eigenschaft
 * oder Datei), Auswahl mit Seed und Export. Ereignisse: `onSizeCalculated`,
 * `onSelectionDrawn`, `onError`.
 */
export function FlowauditSampling(props: FlowauditSamplingProps) {
  const view = useSampling(props)
  const { state, t, controller } = view
  return (
    <div className="fa-sampling" lang={view.locale}>
      {state.busy === 'load' ? <p className="fa-sampling__muted" role="status">{t('loading')}</p> : null}
      {state.error ? <p className="fa-sampling__failure" role="alert">{t('failed', { message: state.error })}</p> : null}
      {state.catalogue ? (
        <>
          <Sizing view={view} locale={props.locale} />
          <SamplingPopulation items={view.population} t={t} locale={view.locale} importLocale={props.locale} onImport={controller.usePopulation} />
          <Selection view={view} locale={props.locale} />
        </>
      ) : null}
    </div>
  )
}
