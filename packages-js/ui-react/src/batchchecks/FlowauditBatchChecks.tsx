import { useEffect, useRef, useState } from 'react'
import { createBatchchecksController, batchchecksMessages, batchchecksIsEmpty, batchchecksRows, type BatchchecksItem, type BatchchecksPort, type Locale } from '@auditcore/ui-core'
import { useTranslation } from '../i18n'
import { classes, useStoreState } from '../store'

export interface FlowauditBatchChecksProps {
  port?: BatchchecksPort | null
  locale?: Locale
  onItemSelect?: (item: BatchchecksItem) => void
  onError?: (message: string) => void
}

/**
 * BatchChecks als native React-Komponente (Vertrag wie `<flowaudit-batch-checks>`):
 * Liste mit Auswahl. Ereignisse: `onItemSelect`, `onError`.
 */
export function FlowauditBatchChecks(props: FlowauditBatchChecksProps) {
  const { t, locale } = useTranslation(batchchecksMessages, props.locale)
  const latest = useRef(props)
  latest.current = props
  const [controller] = useState(() =>
    createBatchchecksController({
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
  const rows = batchchecksRows(state)
  return (
    <section className="fa-batchchecks" lang={locale} aria-label={t('title')}>
      {state.busy === 'load' ? <p className="fa-batchchecks__muted" role="status">{t('loading')}</p> : null}
      {state.error ? <p className="fa-batchchecks__failure" role="alert">{t('failed', { message: state.error })}</p> : null}
      {batchchecksIsEmpty(state) ? <p className="fa-batchchecks__muted">{t('empty')}</p> : null}
      {rows.length ? (
        <ul className="fa-batchchecks__list">
          {rows.map((row) => (
            <li key={row.id}>
              <button type="button" className={classes('fa-batchchecks__item', row.selected && 'fa-batchchecks__item--selected')} aria-pressed={row.selected} onClick={() => controller.select(row.id)}>{row.label}</button>
            </li>
          ))}
        </ul>
      ) : null}
    </section>
  )
}
