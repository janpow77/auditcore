import { useEffect, useRef, useState } from 'react'
import {
  createRedactionController,
  redactionMessages,
  type Locale,
  type RedactionController,
  type RedactionData,
  type RedactionPlan,
  type RedactionPort,
  type RedactionResult,
  type RedactionTranslate,
  type RedactionUrls,
} from '@auditcore/ui-core'
import { useTranslation } from '../i18n'
import { useStoreState } from '../store'

export interface RedactionInputs {
  port?: RedactionPort | null
  locale?: Locale
  /** Objekt-URLs für Seitenbild und Download (Standard: `URL.createObjectURL`). */
  urls?: RedactionUrls
  /** Von der Anwendung bereitgestellte PDF; das Dateifeld entfällt. */
  file?: Blob | null
  /** Dateiname zu `file` (Standard: Name der Datei oder `dokument.pdf`). */
  filename?: string
  /** Startwerte der eigenen Begriffe (änderbar). */
  terms?: readonly string[]
  /** Startwerte der Muster (Kennungen aus dem Katalog, änderbar). */
  patterns?: readonly string[]
  onRedactionPlanned?: (plan: RedactionPlan) => void
  onRedactionCompleted?: (result: RedactionResult) => void
  onError?: (message: string) => void
}

export interface UseRedaction {
  t: RedactionTranslate
  locale: Locale
  controller: RedactionController
  state: RedactionData
}

/** React-Anbindung von „PDF schwärzen“ aus `@auditcore/ui-core` (dieselbe Logik wie `useRedaction` in Vue). */
export function useRedaction(props: RedactionInputs): UseRedaction {
  const { t, locale } = useTranslation(redactionMessages, props.locale)
  const latest = useRef(props)
  latest.current = props
  const [controller] = useState(() =>
    createRedactionController({
      port: () => latest.current.port ?? null,
      urls: props.urls,
      callbacks: () => ({
        planned: (plan) => latest.current.onRedactionPlanned?.(plan),
        completed: (result) => latest.current.onRedactionCompleted?.(result),
        failed: (message) => latest.current.onError?.(message),
      }),
    }),
  )
  const state = useStoreState(controller.store)
  useEffect(() => {
    void controller.load()
  }, [controller, props.port])
  useEffect(() => {
    controller.provideFile(props.file ?? null, props.filename)
  }, [controller, props.file, props.filename])
  // Vorgaben nur bei geändertem Inhalt übernehmen, nicht bei jedem neuen Array.
  const presetKey = JSON.stringify([props.terms ?? null, props.patterns ?? null])
  useEffect(() => {
    const [terms, patterns] = JSON.parse(presetKey) as [string[] | null, string[] | null]
    if (terms || patterns) controller.presetCriteria({ terms: terms ?? undefined, patterns: patterns ?? undefined })
  }, [controller, presetKey])
  useEffect(() => () => controller.dispose(), [controller])
  return { t, locale, controller, state }
}
