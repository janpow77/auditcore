import { useEffect, useRef, useState } from 'react'
import {
  benfordMessages,
  benfordProfile,
  benfordValues,
  createBenfordController,
  type BenfordAnalysis,
  type BenfordController,
  type BenfordData,
  type BenfordMetricsRequest,
  type BenfordPort,
  type BenfordTranslate,
  type ConformityProfile,
  type Locale,
} from '@auditcore/ui-core'
import { useTranslation } from '../i18n'
import { useStoreState } from '../store'

/** Leere Werteliste als feste Referenz (sonst setzte jeder Render den Import zurück). */
const NO_VALUES: readonly (number | null)[] = []

export interface BenfordInputs {
  port?: BenfordPort | null
  values?: readonly (number | null)[]
  locale?: Locale
  /** Zusätzliche Kennzahlen (Chi²-Test, auffällige Ziffern) mit ihren Parametern. */
  metrics?: BenfordMetricsRequest | null
  /** Nach dem Laden und bei neuen Werten sofort analysieren. */
  autoAnalyse?: boolean
  /** Werte und Formular ausblenden (Einbettung in Berichte, mit `autoAnalyse`). */
  hideInputs?: boolean
  onAnalysisCompleted?: (result: BenfordAnalysis) => void
  onError?: (message: string) => void
}

export interface UseBenford {
  t: BenfordTranslate
  locale: Locale
  controller: BenfordController
  state: BenfordData
  values: readonly (number | null)[]
  profile: ConformityProfile | null
}

/** React-Anbindung der Benford-Analyse aus `@auditcore/ui-core` (dieselbe Logik wie `useBenford` in Vue). */
export function useBenford(props: BenfordInputs): UseBenford {
  const { t, locale } = useTranslation(benfordMessages, props.locale)
  const latest = useRef(props)
  latest.current = props
  const [controller] = useState(() =>
    createBenfordController({
      port: () => latest.current.port ?? null,
      values: () => latest.current.values ?? NO_VALUES,
      callbacks: () => ({
        analysed: (result) => latest.current.onAnalysisCompleted?.(result),
        failed: (message) => latest.current.onError?.(message),
      }),
      metrics: () => latest.current.metrics,
      autoAnalyse: () => latest.current.autoAnalyse,
    }),
  )
  const state = useStoreState(controller.store)
  const given = props.values ?? NO_VALUES
  useEffect(() => {
    void controller.load()
  }, [controller, props.port])
  useEffect(() => {
    void controller.valuesChanged()
  }, [controller, given])
  return { t, locale, controller, state, values: benfordValues(state, given), profile: benfordProfile(state) }
}
