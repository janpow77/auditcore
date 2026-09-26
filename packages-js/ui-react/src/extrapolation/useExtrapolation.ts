import { useEffect, useRef, useState } from 'react'
import {
  createExtrapolationController,
  extrapolationInputNumber,
  extrapolationMessages,
  extrapolationMethod,
  type EvaluationResult,
  type ExtrapolationController,
  type ExtrapolationData,
  type ExtrapolationMethod,
  type ExtrapolationPort,
  type ExtrapolationTranslate,
  type Locale,
  type ResidualResult,
  type StratumInput,
  type UnitInput,
} from '@flowaudit/ui-core'
import { useTranslation } from '../i18n'
import { useStoreState } from '../store'

/** Leere Listen als feste Referenzen (sonst setzte jeder Render die Eingaben zurück). */
const NO_STRATA: readonly StratumInput[] = []
const NO_UNITS: readonly UnitInput[] = []

export interface ExtrapolationInputs {
  port?: ExtrapolationPort | null
  strata?: readonly StratumInput[]
  units?: readonly UnitInput[]
  locale?: Locale
  onEvaluationCompleted?: (result: EvaluationResult) => void
  onResidualComputed?: (result: ResidualResult) => void
  onError?: (message: string) => void
}

export interface UseExtrapolation {
  t: ExtrapolationTranslate
  locale: Locale
  controller: ExtrapolationController
  state: ExtrapolationData
  method: ExtrapolationMethod | null
}

/** React-Anbindung der Hochrechnung aus `@flowaudit/ui-core` (dieselbe Logik wie `useExtrapolation` in Vue). */
export function useExtrapolation(props: ExtrapolationInputs): UseExtrapolation {
  const { t, locale } = useTranslation(extrapolationMessages, props.locale)
  const latest = useRef({ props, locale })
  latest.current = { props, locale }
  const [controller] = useState(() =>
    createExtrapolationController({
      port: () => latest.current.props.port ?? null,
      strata: () => latest.current.props.strata ?? NO_STRATA,
      units: () => latest.current.props.units ?? NO_UNITS,
      format: (value) => extrapolationInputNumber(latest.current.locale)(value),
      callbacks: () => ({
        evaluated: (result) => latest.current.props.onEvaluationCompleted?.(result),
        residualComputed: (result) => latest.current.props.onResidualComputed?.(result),
        failed: (message) => latest.current.props.onError?.(message),
      }),
    }),
  )
  const state = useStoreState(controller.store)
  const strata = props.strata ?? NO_STRATA
  const units = props.units ?? NO_UNITS
  const loaded = state.catalogue !== null
  useEffect(() => {
    void controller.load()
  }, [controller, props.port])
  useEffect(() => {
    if (loaded) controller.applyInputs()
  }, [controller, strata, units, loaded])
  return { t, locale, controller, state, method: extrapolationMethod(state) }
}
