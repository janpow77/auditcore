import { useEffect, useRef, useState } from 'react'
import type { DownloadFile } from '@flowaudit/common'
import {
  createReportingController,
  reportingMessages,
  reportingProfile,
  type FormatProfile,
  type Locale,
  type ReportingController,
  type ReportingData,
  type ReportingPort,
  type ReportingTranslate,
  type ReportTableInput,
  type WorkbookPreview,
} from '@flowaudit/ui-core'
import { useTranslation } from '../i18n'
import { useStoreState } from '../store'

/** Leere Tabellenliste als feste Referenz (sonst veraltete jede Vorschau bei jedem Render). */
const NO_TABLES: readonly ReportTableInput[] = []

export interface ReportExportInputs {
  port?: ReportingPort | null
  tables?: readonly ReportTableInput[]
  filename?: string
  locale?: Locale
  onPreviewCompleted?: (result: WorkbookPreview) => void
  onExportCompleted?: (file: DownloadFile) => void
  onError?: (message: string) => void
}

export interface UseReportExport {
  t: ReportingTranslate
  locale: Locale
  controller: ReportingController
  state: ReportingData
  tables: readonly ReportTableInput[]
  profile: FormatProfile | null
}

/** React-Anbindung des Tabellenexports aus `@flowaudit/ui-core` (dieselbe Logik wie `useReportExport` in Vue). */
export function useReportExport(props: ReportExportInputs): UseReportExport {
  const { t, locale } = useTranslation(reportingMessages, props.locale)
  const latest = useRef(props)
  latest.current = props
  const [controller] = useState(() =>
    createReportingController({
      port: () => latest.current.port ?? null,
      tables: () => latest.current.tables ?? NO_TABLES,
      callbacks: () => ({
        previewed: (result) => latest.current.onPreviewCompleted?.(result),
        exported: (file) => latest.current.onExportCompleted?.(file),
        failed: (message) => latest.current.onError?.(message),
      }),
    }),
  )
  const state = useStoreState(controller.store)
  const tables = props.tables ?? NO_TABLES
  const filename = props.filename ?? ''
  useEffect(() => {
    void controller.load()
  }, [controller, props.port])
  useEffect(() => controller.setFilename(filename), [controller, filename])
  const first = useRef(true)
  useEffect(() => {
    if (first.current) first.current = false
    else controller.tablesChanged()
  }, [controller, tables])
  return { t, locale, controller, state, tables, profile: reportingProfile(state) }
}
