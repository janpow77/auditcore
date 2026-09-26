import { useEffect, useMemo, useRef, useState } from 'react'
import {
  createRiskController,
  riskMessages,
  selectRisk,
  type Evaluation,
  type Locale,
  type ProfileDetail,
  type RiskController,
  type RiskData,
  type RiskInputs,
  type RiskPort,
  type RiskSelection,
  type RiskTranslate,
} from '@auditcore/ui-core'
import { useTranslation } from '../i18n'
import { useStoreState } from '../store'

export interface UseRiskFlags {
  t: RiskTranslate
  controller: RiskController
  state: RiskData
  selection: RiskSelection
}

/** React-Anbindung des Zustandsautomaten aus `@auditcore/ui-core` (dieselbe Logik wie `useRiskFlags`/`useRiskProfile` in Vue). */
export function useRiskFlags(props: { evaluation?: Evaluation | null; profile?: ProfileDetail | null; port?: RiskPort | null; locale?: Locale }): UseRiskFlags {
  const { t } = useTranslation(riskMessages, props.locale)
  const [controller] = useState(createRiskController)
  const state = useStoreState(controller.store)
  const { evaluation, profile, port } = props
  const latest = useRef<RiskInputs>({ evaluation, profile, port })
  latest.current = { evaluation, profile, port }
  useEffect(() => controller.resetSelection(), [controller, evaluation])
  useEffect(() => {
    void controller.loadProfile({ evaluation, profile, port }, () => latest.current)
  }, [controller, evaluation, profile, port])
  const recordText = t('colRecord')
  const selection = useMemo(() => selectRisk(state, evaluation, recordText), [state, evaluation, recordText])
  return { t, controller, state, selection }
}
