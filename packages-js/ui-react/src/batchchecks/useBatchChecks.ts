import { useEffect, useRef, useState } from 'react'
import {
  batchchecksMessages,
  createBatchchecksController,
  type BatchchecksAnswer,
  type BatchchecksController,
  type BatchchecksData,
  type BatchchecksPort,
  type BatchchecksTranslate,
  type Locale,
  type TableImportData,
} from '@auditcore/ui-core'
import { useTranslation } from '../i18n'
import { useStoreState } from '../store'

export interface BatchChecksInputs {
  port?: BatchchecksPort | null
  result?: BatchchecksAnswer | null
  locale?: Locale
  onChecksCompleted?: (answer: BatchchecksAnswer) => void
  onError?: (message: string) => void
}

export interface UseBatchChecks {
  t: BatchchecksTranslate
  locale: Locale
  controller: BatchchecksController
  state: BatchchecksData
  table: TableImportData
}

/** React-Anbindung der Bestandsprüfung aus `@auditcore/ui-core` (dieselbe Logik wie `useBatchChecks` in Vue). */
export function useBatchChecks(props: BatchChecksInputs): UseBatchChecks {
  const { t, locale } = useTranslation(batchchecksMessages, props.locale)
  const latest = useRef(props)
  latest.current = props
  const [controller] = useState(() =>
    createBatchchecksController({
      port: () => latest.current.port ?? null,
      callbacks: () => ({
        completed: (answer) => latest.current.onChecksCompleted?.(answer),
        failed: (message) => latest.current.onError?.(message),
      }),
    }),
  )
  const state = useStoreState(controller.store)
  const table = useStoreState(controller.table.store)
  useEffect(() => {
    void controller.load()
  }, [controller, props.port])
  const given = props.result ?? null
  useEffect(() => controller.showAnswer(given), [controller, given])
  return { t, locale, controller, state, table }
}
