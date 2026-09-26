import { useEffect, useMemo, useRef, useState } from 'react'
import {
  buildSynopsisExport,
  createSynopsisController,
  selectSynopsis,
  synopsisBase,
  synopsisMessages,
  type ClientExportFormat,
  type ExportPayload,
  type Locale,
  type SynopsisController,
  type SynopsisData,
  type SynopsisInputs,
  type SynopsisSelection,
  type SynopsisTranslate,
} from '@flowaudit/ui-core'
import { useTranslation } from '../i18n'
import { useStoreState } from '../store'

export interface UseSynopsis {
  t: SynopsisTranslate
  locale: Locale
  controller: SynopsisController
  state: SynopsisData
  inputs: SynopsisInputs
  selection: SynopsisSelection
  exportAs: (format: ClientExportFormat) => ExportPayload | null
}

/** React-Anbindung des Zustandsautomaten aus `@flowaudit/ui-core` (dieselbe Logik wie `useSynopsis` in Vue). */
export function useSynopsis(props: SynopsisInputs & { locale?: Locale }): UseSynopsis {
  const { t, locale } = useTranslation(synopsisMessages, props.locale)
  const translate = useRef(t)
  translate.current = t
  const [controller] = useState(() => createSynopsisController(() => translate.current))
  const state = useStoreState(controller.store)
  const { comparison, result, comparisonId, port, title, oldLabel, newLabel } = props
  const inputs = useMemo<SynopsisInputs>(
    () => ({ comparison, result, comparisonId, port, title, oldLabel, newLabel }),
    [comparison, result, comparisonId, port, title, oldLabel, newLabel],
  )
  const latest = useRef(inputs)
  latest.current = inputs
  useEffect(() => {
    void controller.reload(latest.current)
  }, [controller, comparisonId, port])
  const base = synopsisBase(state, inputs)
  useEffect(() => controller.resetOverrides(), [controller, base])
  const selection = useMemo(() => selectSynopsis(state, inputs, t), [state, inputs, t])
  const exportAs = (format: ClientExportFormat): ExportPayload | null => buildSynopsisExport(selection, format, t, locale)
  return { t, locale, controller, state, inputs, selection, exportAs }
}
