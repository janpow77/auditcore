import { useEffect, useRef, useState } from 'react'
import { createScreeningController, selectScreening, type ReviewEvents, type ScreeningController, type ScreeningData, type ScreeningPort, type ScreeningSelection } from '@flowaudit/ui-core'
import { useStoreState } from '../store'

export interface UseScreeningReview {
  controller: ScreeningController
  state: ScreeningData
  selection: ScreeningSelection
}

/**
 * React-Anbindung des Zustandsautomaten aus `@flowaudit/ui-core` (dieselbe Logik
 * wie `useScreeningReview` in Vue). Lädt bei gesetztem Port Einstellungen,
 * Quellen und Läufe und öffnet danach `runId`.
 */
export function useScreeningReview(port: ScreeningPort | null | undefined, runId: string, events: ReviewEvents): UseScreeningReview {
  const latest = useRef({ port, runId, events })
  latest.current = { port, runId, events }
  const [controller] = useState(() => createScreeningController(() => latest.current.port, () => latest.current.events))
  const state = useStoreState(controller.store)
  useEffect(() => {
    if (!port) return
    void (async () => {
      await controller.load()
      if (latest.current.runId) await controller.openRun(latest.current.runId)
    })()
  }, [controller, port])
  return { controller, state, selection: selectScreening(state) }
}
