import { useEffect, useMemo, useRef, useState } from 'react'
import {
  comparisonsMessages,
  comparisonsView,
  createComparisonsController,
  DEFAULT_MAX_UPLOAD_BYTES,
  type Comparison,
  type ComparisonsController,
  type ComparisonsData,
  type ComparisonsError,
  type ComparisonsPort,
  type ComparisonsTranslate,
  type ComparisonsView,
  type Locale,
} from '@auditcore/ui-core'
import { useTranslation } from '../i18n'
import { useStoreState } from '../store'

export interface ComparisonsInputs {
  /** Datenzugang, z. B. `createSynopsisRestClient({ baseUrl: '/api/synopsis' })` (auditcore_documents.web). */
  port?: ComparisonsPort | null
  /** Größte Datei je Seite in Byte; wie `ServiceSettings.max_upload_bytes` des Servers. */
  maxUploadBytes?: number
  locale?: Locale
  onComparisonCreated?: (comparison: Comparison) => void
  onComparisonImported?: (comparison: Comparison) => void
  onComparisonRemoved?: (id: string) => void
  onError?: (error: ComparisonsError) => void
}

export interface UseComparisons {
  t: ComparisonsTranslate
  locale: Locale
  controller: ComparisonsController
  state: ComparisonsData
  view: ComparisonsView
}

/** React-Anbindung der Vergleichsverwaltung aus `@auditcore/ui-core` (dieselbe Logik wie `useComparisons` in Vue). */
export function useComparisons(props: ComparisonsInputs): UseComparisons {
  const { t, locale } = useTranslation(comparisonsMessages, props.locale)
  const latest = useRef({ props, t, locale })
  latest.current = { props, t, locale }
  const [controller] = useState(() =>
    createComparisonsController({
      port: () => latest.current.props.port ?? null,
      t: () => latest.current.t,
      lang: () => latest.current.locale,
      maxBytes: () => latest.current.props.maxUploadBytes ?? DEFAULT_MAX_UPLOAD_BYTES,
      onCreated: (comparison) => latest.current.props.onComparisonCreated?.(comparison),
      onImported: (comparison) => latest.current.props.onComparisonImported?.(comparison),
      onRemoved: (id) => latest.current.props.onComparisonRemoved?.(id),
      onError: (error) => latest.current.props.onError?.(error),
    }),
  )
  const state = useStoreState(controller.store)
  useEffect(() => {
    void controller.load()
  }, [controller, props.port])
  const maxBytes = props.maxUploadBytes ?? DEFAULT_MAX_UPLOAD_BYTES
  const view = useMemo(() => comparisonsView(state, t, { lang: locale, maxBytes }), [state, t, locale, maxBytes])
  return { t, locale, controller, state, view }
}
