import { screeningMessages, type Locale, type ScreeningError, type ScreeningPort } from '@auditcore/ui-core'
import { LocaleProvider, useTranslation } from '../i18n'
import { ScreeningRunDetail } from './ScreeningRunDetail'
import { ScreeningRunForm } from './ScreeningRunForm'
import { ScreeningRunList } from './ScreeningRunList'
import { ScreeningSources } from './ScreeningSources'
import { useScreeningReview, type UseScreeningReview } from './useScreeningReview'

export interface FlowauditScreeningReviewProps {
  /** Datenzugang (Vertrag screening_review/1), z. B. `createScreeningRestPort({ baseUrl: '/api/screening' })`. */
  port?: ScreeningPort | null
  /** Beim Laden zu öffnender Prüflauf. */
  runId?: string
  locale?: Locale
  /** Ereignis `run-created` der Vue-Fassung. */
  onRunCreated?: (detail: { runId: string }) => void
  /** Ereignis `decided` der Vue-Fassung. */
  onDecided?: (detail: { runId: string; hitId: string; status: string }) => void
  /** Ereignis `error` der Vue-Fassung. */
  onError?: (detail: ScreeningError) => void
}

function Sidebar({ state, controller }: Pick<UseScreeningReview, 'state' | 'controller'>) {
  const { settings, sources, run } = state
  return (
    <aside>
      {settings && sources ? <ScreeningRunForm settings={settings} sources={sources.sources} busy={state.busy} onSubmit={(request) => void controller.createRun(request)} /> : null}
      <ScreeningRunList runs={state.runs} activeId={run?.run_id ?? null} onOpen={(id) => void controller.openRun(id)} />
      {sources ? <ScreeningSources compact sources={sources.sources} checkedAt={sources.checked_at} /> : null}
    </aside>
  )
}

/**
 * Screening-Trefferprüfung (Sanktionslisten, PEP) als native React-Komponente –
 * Vertrag, Texte und Ablauf wie `<flowaudit-screening-review>`: Prüflauf
 * anlegen, Treffer filtern, vergleichen, entscheiden, Zweitprüfung, Protokoll.
 */
export function FlowauditScreeningReview(props: FlowauditScreeningReviewProps) {
  const { t, locale } = useTranslation(screeningMessages, props.locale)
  const { controller, state, selection } = useScreeningReview(props.port, props.runId ?? '', {
    onRunCreated: (run) => props.onRunCreated?.({ runId: run.run_id }),
    onDecided: (detail) => props.onDecided?.(detail),
    onError: (error) => props.onError?.(error),
    networkMessage: (message) => t('networkError', { message }),
  })
  const { settings, run } = state
  return (
    <LocaleProvider locale={locale}>
      <div className="fa-screening" aria-busy={state.busy} data-testid="screening-review">
        <header className="fa-screening__header">
          <h2>{t('title')}</h2>
          <span className="fa-screening__notice">{t('notice')}</span>
        </header>
        {props.port ? null : <p className="fa-screening__alert" role="alert">{t('noPort')}</p>}
        {state.error ? <p className="fa-screening__alert" role="alert">{state.error.message}</p> : null}
        <div className="fa-screening__layout">
          <Sidebar state={state} controller={controller} />
          <div>
            {run ? (
              <ScreeningRunDetail
                run={run}
                subjects={selection.visibleSubjects}
                selected={selection.selected}
                filter={state.filter}
                settings={settings}
                events={state.log?.events ?? []}
                busy={state.busy}
                onFilterChange={controller.setFilter}
                onSelect={controller.select}
                onNext={controller.selectNext}
                onDecide={(outcome, reason, fourEyes) => void controller.decide(outcome, reason, fourEyes)}
                onSecondReview={(approve, reason) => void controller.secondReview(approve, reason)}
              />
            ) : <p className="fa-screening__panel fa-screening__empty">{t('selectRun')}</p>}
          </div>
        </div>
      </div>
    </LocaleProvider>
  )
}
