import { forwardRef, useImperativeHandle, type Ref } from 'react'
import { synopsisPortOf } from '@auditcore/ui-core'
import { Button } from '../base/Button'
import { Dialog } from '../base/Dialog'
import { LocaleProvider } from '../i18n'
import { classes, useElementId } from '../store'
import { FlowauditSynopsis } from '../synopsis/FlowauditSynopsis'
import { ComparisonForm } from './ComparisonForm'
import { ComparisonList } from './ComparisonList'
import { useComparisons, type ComparisonsInputs, type UseComparisons } from './useComparisons'

export interface FlowauditComparisonsProps extends ComparisonsInputs {
  /** `false`: nur Liste und Ansicht, kein Hochladen, Import oder Löschen. */
  editable?: boolean
  /** Geöffneten Vergleich als Synopse einbetten (braucht `port.load`); sonst nur `onComparisonOpen`. */
  showSynopsis?: boolean
  onComparisonOpen?: (id: string) => void
}

export interface FlowauditComparisonsHandle {
  reload: () => Promise<void>
  open: (id: string) => void
}

function Workspace({ props, view, open }: { props: FlowauditComparisonsProps; view: UseComparisons; open: (id: string) => void }) {
  const { controller, state, t } = view
  const { port, editable = true } = props
  if (!port) return <div className={classes('fa-comparisons__layout', !editable && 'fa-comparisons__layout--single')} />
  return (
    <div className={classes('fa-comparisons__layout', !editable && 'fa-comparisons__layout--single')}>
      {editable ? (
        <ComparisonForm
          form={state.form} view={view.view} t={t} busy={state.busy === 'create'}
          onFormUpdate={controller.updateForm} onSectionToggle={controller.toggleSection}
          onFormSubmit={() => void controller.submit()} onFormReset={controller.resetForm}
        />
      ) : null}
      <ComparisonList
        rows={view.view.rows} query={state.query} countText={view.view.countText} emptyText={view.view.emptyText} busy={state.busy !== null}
        editable={editable} canImport={Boolean(port.importResult)} t={t}
        onQueryChange={controller.setQuery} onComparisonOpen={open} onComparisonRemove={controller.askRemove} onResultImport={(text) => void controller.importText(text)}
      />
    </div>
  )
}

function RemoveDialog({ view }: { view: UseComparisons }) {
  const { controller, state, t } = view
  const title = view.view.pendingTitle
  const footer = (
    <>
      <Button variant="ghost" onClick={controller.cancelRemove}>{t('cancel')}</Button>
      <Button variant="danger" icon="trash" loading={state.busy === 'remove'} testId="comparisons-confirm-remove" onClick={() => void controller.confirmRemove()}>{t('remove')}</Button>
    </>
  )
  return (
    <Dialog open={title !== null} title={t('confirmTitle')} size="sm" locale={view.locale} onClose={controller.cancelRemove} footer={footer}>
      <p className="fa-comparisons__confirm">{t('confirmText', { title: title ?? '' })}</p>
    </Dialog>
  )
}

/**
 * Dokumentvergleiche als native React-Komponente (Vertrag wie `<flowaudit-comparisons>`):
 * zwei Fassungen hochladen, gespeicherte Vergleiche suchen, öffnen (eingebettete Synopse),
 * löschen und fertige Ergebnisse importieren – über `auditcore_documents.web`.
 */
export const FlowauditComparisons = forwardRef(function FlowauditComparisons(props: FlowauditComparisonsProps, ref: Ref<FlowauditComparisonsHandle>) {
  const view = useComparisons(props)
  const { controller, state, t } = view
  const headingId = useElementId('fa-comparisons')
  const synopsisPort = props.showSynopsis === false ? null : synopsisPortOf(props.port)
  const open = (id: string): void => {
    if (synopsisPort) controller.open(id)
    props.onComparisonOpen?.(id)
  }
  useImperativeHandle(ref, () => ({ reload: controller.load, open }))
  const embedded = synopsisPort !== null && state.openId !== null
  return (
    <LocaleProvider locale={view.locale}>
      <section className="fa-comparisons" aria-labelledby={headingId} aria-busy={state.busy !== null || undefined}>
        <header className="fa-comparisons__head">
          <h2 id={headingId} className="fa-comparisons__heading">{t('title')}</h2>
          <p className="fa-comparisons__note">{t('workAid')}</p>
        </header>
        <p className="fa-sr-only" role="status" aria-live="polite">{view.view.busyText || state.notice}</p>
        {!props.port ? <p className="fa-comparisons__state fa-comparisons__state--error" role="alert">{t('noPort')}</p>
          : state.error ? <p className="fa-comparisons__state fa-comparisons__state--error" role="alert">{state.error.message}</p> : null}
        {embedded ? (
          <div className="fa-comparisons__open">
            <Button size="sm" variant="secondary" onClick={() => controller.open(null)}>{t('back')}</Button>
            <FlowauditSynopsis comparisonId={state.openId ?? undefined} port={synopsisPort} editable={props.editable ?? true} locale={view.locale} />
          </div>
        ) : <Workspace props={props} view={view} open={open} />}
        <RemoveDialog view={view} />
      </section>
    </LocaleProvider>
  )
})
