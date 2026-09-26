import { useEffect, useRef, useState } from 'react'
import {
  createSamplingController,
  samplingInputNumber,
  samplingMessages,
  samplingPopulation,
  samplingProfile,
  type Locale,
  type MethodProfile,
  type PopulationItem,
  type SamplingController,
  type SamplingData,
  type SamplingPort,
  type SamplingTranslate,
  type SelectionResult,
  type SizeResult,
} from '@flowaudit/ui-core'
import { useTranslation } from '../i18n'
import { useStoreState } from '../store'

/** Leere Grundgesamtheit als feste Referenz (sonst setzte jeder Render den Import zurück). */
const NO_ITEMS: readonly PopulationItem[] = []

export interface SamplingInputs {
  port?: SamplingPort | null
  items?: readonly PopulationItem[]
  locale?: Locale
  onSizeCalculated?: (result: SizeResult) => void
  onSelectionDrawn?: (result: SelectionResult) => void
  onError?: (message: string) => void
}

export interface UseSampling {
  t: SamplingTranslate
  locale: Locale
  controller: SamplingController
  state: SamplingData
  profile: MethodProfile | null
  population: readonly PopulationItem[]
}

/** React-Anbindung des Stichprobenrechners aus `@flowaudit/ui-core` (dieselbe Logik wie `useSampling` in Vue). */
export function useSampling(props: SamplingInputs): UseSampling {
  const { t, locale } = useTranslation(samplingMessages, props.locale)
  const latest = useRef({ props, locale })
  latest.current = { props, locale }
  const [controller] = useState(() =>
    createSamplingController({
      port: () => latest.current.props.port ?? null,
      items: () => latest.current.props.items ?? NO_ITEMS,
      format: (value) => samplingInputNumber(latest.current.locale)(value),
      callbacks: () => ({
        sizeCalculated: (result) => latest.current.props.onSizeCalculated?.(result),
        selectionDrawn: (result) => latest.current.props.onSelectionDrawn?.(result),
        failed: (message) => latest.current.props.onError?.(message),
      }),
    }),
  )
  const state = useStoreState(controller.store)
  const items = props.items ?? NO_ITEMS
  useEffect(() => {
    void controller.load()
  }, [controller, props.port])
  useEffect(() => controller.usePopulation(null), [controller, items])
  return { t, locale, controller, state, profile: samplingProfile(state), population: samplingPopulation(state, items) }
}
