import { useEffect, useRef, useState, type KeyboardEvent } from 'react'
import { createRunnerController, runnerHinweise, runnerMessages, runnerMeta, runnerNachbarTab, runnerTabs, type Locale, type RunnerAnsicht, type RunnerPort } from '@auditcore/ui-core'
import { useTranslation } from '../i18n'
import { classes, useElementId, useStoreState } from '../store'
import { ProfilFormular } from './parts/ProfilFormular'
import { StatusBereich } from './parts/StatusBereich'
import { WerkzeugBereich } from './parts/WerkzeugBereich'

export interface FlowauditRunnerConsoleProps {
  /** Fachlogik, z. B. `createRunnerRestPort({ baseUrl: '/api' })`; hat Vorrang vor `api`. */
  port?: RunnerPort | null
  /** Basis-URL der JSON-API von `auditcore-runner ui`. */
  api?: string
  /** Bereich beim Öffnen. */
  ansicht?: RunnerAnsicht
  locale?: Locale
  onApplied?: (version: number) => void
  onError?: (message: string) => void
}

function useRunnerController(props: FlowauditRunnerConsoleProps) {
  const latest = useRef(props)
  latest.current = props
  const [controller] = useState(() => {
    const created = createRunnerController({
      port: () => latest.current.port ?? null,
      api: () => latest.current.api ?? '',
      callbacks: () => ({
        applied: (version) => latest.current.onApplied?.(version),
        failed: (message) => latest.current.onError?.(message),
      }),
    })
    created.zeige(props.ansicht ?? 'status')
    return created
  })
  useEffect(() => {
    void controller.load()
  }, [controller, props.port, props.api])
  return controller
}

/**
 * Runner-Konsole als native React-Komponente (Vertrag wie `<flowaudit-runner-console>`):
 * Status, Einstellungen, Werkzeuge und Prioritäten eines Rechners mit `auditcore_runner`.
 * Ereignisse: `onApplied`, `onError`.
 */
export function FlowauditRunnerConsole(props: FlowauditRunnerConsoleProps) {
  const { t, locale } = useTranslation(runnerMessages, props.locale)
  const uid = useElementId('fa-runner')
  const controller = useRunnerController(props)
  const state = useStoreState(controller.store)
  const meta = runnerMeta(state, t)
  const hinweise = runnerHinweise(state, t)
  const bereich = { state, controller, t }

  function tabTaste(event: KeyboardEvent<HTMLDivElement>): void {
    const richtung = event.key === 'ArrowRight' ? 1 : event.key === 'ArrowLeft' ? -1 : 0
    if (!richtung) return
    event.preventDefault()
    const next = runnerNachbarTab(state.ansicht, richtung)
    controller.zeige(next)
    document.getElementById(`${uid}-tab-${next}`)?.focus()
  }

  return (
    <section className="fa-runner" lang={locale} aria-label={t('title')}>
      <header className="fa-runner__kopf">
        <h2 className="fa-runner__titel">{t('title')}</h2>
        {meta ? <p className="fa-runner__meta">{meta}</p> : null}
      </header>
      <div className="fa-runner__reiter" role="tablist" aria-label={t('tabs')} onKeyDown={tabTaste}>
        {runnerTabs(state, t).map((tab) => (
          <button key={tab.id} id={`${uid}-tab-${tab.id}`} type="button" role="tab" className="fa-runner__tab" aria-selected={tab.selected ? 'true' : 'false'} aria-controls={`${uid}-panel`} tabIndex={tab.selected ? 0 : -1} onClick={() => controller.zeige(tab.id)}>{tab.label}</button>
        ))}
      </div>
      {state.busy ? <p className="fa-runner__muted" role="status">{state.busy === 'load' ? t('loading') : t('working')}</p> : null}
      {state.error ? <p className="fa-runner__failure" role="alert">{t('failed', { message: state.error })}</p> : null}
      {state.meldung ? <p className={classes('fa-runner__meldung', `fa-runner__meldung--${state.meldung.ton}`)} role="status">{t(state.meldung.key, state.meldung.params)}</p> : null}
      <div id={`${uid}-panel`} className="fa-runner__panel" role="tabpanel" aria-labelledby={`${uid}-tab-${state.ansicht}`} tabIndex={0}>
        {hinweise.length ? (
          <ul className="fa-runner__hinweise">
            {hinweise.map((hinweis) => <li key={hinweis.text} className={classes('fa-runner__hinweis', `fa-runner__hinweis--${hinweis.ton}`)}>{hinweis.text}</li>)}
          </ul>
        ) : null}
        {state.ansicht === 'status' ? <StatusBereich {...bereich} /> : state.ansicht === 'werkzeuge' ? <WerkzeugBereich {...bereich} /> : <ProfilFormular {...bereich} uid={uid} />}
      </div>
    </section>
  )
}
