import { useEffect, useRef, useState } from 'react'
import { createRunnerController, runnerMessages, runnerIsEmpty, runnerRows, type RunnerItem, type RunnerPort, type Locale } from '@auditcore/ui-core'
import { useTranslation } from '../i18n'
import { classes, useStoreState } from '../store'

export interface FlowauditRunnerConsoleProps {
  port?: RunnerPort | null
  locale?: Locale
  onItemSelect?: (item: RunnerItem) => void
  onError?: (message: string) => void
}

/**
 * RunnerConsole als native React-Komponente (Vertrag wie `<flowaudit-runner-console>`):
 * Liste mit Auswahl. Ereignisse: `onItemSelect`, `onError`.
 */
export function FlowauditRunnerConsole(props: FlowauditRunnerConsoleProps) {
  const { t, locale } = useTranslation(runnerMessages, props.locale)
  const latest = useRef(props)
  latest.current = props
  const [controller] = useState(() =>
    createRunnerController({
      port: () => latest.current.port ?? null,
      callbacks: () => ({
        selected: (item) => latest.current.onItemSelect?.(item),
        failed: (message) => latest.current.onError?.(message),
      }),
    }),
  )
  const state = useStoreState(controller.store)
  useEffect(() => {
    void controller.load()
  }, [controller, props.port])
  const rows = runnerRows(state)
  return (
    <section className="fa-runner" lang={locale} aria-label={t('title')}>
      {state.busy === 'load' ? <p className="fa-runner__muted" role="status">{t('loading')}</p> : null}
      {state.error ? <p className="fa-runner__failure" role="alert">{t('failed', { message: state.error })}</p> : null}
      {runnerIsEmpty(state) ? <p className="fa-runner__muted">{t('empty')}</p> : null}
      {rows.length ? (
        <ul className="fa-runner__list">
          {rows.map((row) => (
            <li key={row.id}>
              <button type="button" className={classes('fa-runner__item', row.selected && 'fa-runner__item--selected')} aria-pressed={row.selected} onClick={() => controller.select(row.id)}>{row.label}</button>
            </li>
          ))}
        </ul>
      ) : null}
    </section>
  )
}
