import { useEffect, useRef, useState } from 'react'
import {
  createExtractionController,
  extractionMessages,
  type ExtractionController,
  type ExtractionData,
  type ExtractionPort,
  type ExtractionRun,
  type ExtractionTranslate,
  type Locale,
} from '@auditcore/ui-core'
import { useTranslation } from '../i18n'
import { useStoreState } from '../store'

export interface ExtractionInputs {
  port?: ExtractionPort | null
  result?: ExtractionRun | null
  locale?: Locale
  onExtractionCompleted?: (result: ExtractionRun) => void
  onError?: (message: string) => void
}

export interface UseExtraction {
  t: ExtractionTranslate
  locale: Locale
  controller: ExtractionController
  state: ExtractionData
}

/** React-Anbindung der Belegerkennung aus `@auditcore/ui-core` (dieselbe Logik wie `useExtraction` in Vue). */
export function useExtraction(props: ExtractionInputs): UseExtraction {
  const { t, locale } = useTranslation(extractionMessages, props.locale)
  const latest = useRef(props)
  latest.current = props
  const [controller] = useState(() =>
    createExtractionController({
      port: () => latest.current.port ?? null,
      callbacks: () => ({
        completed: (result) => latest.current.onExtractionCompleted?.(result),
        failed: (message) => latest.current.onError?.(message),
      }),
    }),
  )
  const state = useStoreState(controller.store)
  useEffect(() => {
    void controller.load()
  }, [controller, props.port])
  const given = props.result ?? null
  useEffect(() => controller.showResult(given), [controller, given])
  return { t, locale, controller, state }
}
