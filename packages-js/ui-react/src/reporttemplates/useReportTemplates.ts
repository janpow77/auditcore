import { useEffect, useRef, useState } from 'react'
import type { DownloadFile } from '@auditcore/common'
import {
  createReporttemplatesController,
  reporttemplatesMessages,
  type Locale,
  type ReporttemplatesController,
  type ReporttemplatesData,
  type ReporttemplatesPort,
  type TemplateData,
  type TemplateDetail,
  type TemplatePreview,
  type Translate,
  type ReporttemplatesMessageKey,
} from '@auditcore/ui-core'
import { useTranslation } from '../i18n'
import { useStoreState } from '../store'

export interface ReportTemplatesInputs {
  port?: ReporttemplatesPort | null
  data?: TemplateData | null
  filename?: string
  locale?: Locale
  onTemplateSelect?: (detail: TemplateDetail) => void
  onPreviewCompleted?: (result: TemplatePreview) => void
  onReportRendered?: (file: DownloadFile) => void
  onError?: (message: string) => void
}

export interface UseReportTemplates {
  t: Translate<ReporttemplatesMessageKey>
  locale: Locale
  controller: ReporttemplatesController
  state: ReporttemplatesData
  hasData: boolean
}

/** React-Anbindung der Berichtsvorlagen aus `@auditcore/ui-core` (dieselbe Logik wie `ReportTemplates.vue`). */
export function useReportTemplates(props: ReportTemplatesInputs): UseReportTemplates {
  const { t, locale } = useTranslation(reporttemplatesMessages, props.locale)
  const latest = useRef(props)
  latest.current = props
  const [controller] = useState(() =>
    createReporttemplatesController({
      port: () => latest.current.port ?? null,
      data: () => latest.current.data ?? null,
      callbacks: () => ({
        selected: (detail) => latest.current.onTemplateSelect?.(detail),
        previewed: (result) => latest.current.onPreviewCompleted?.(result),
        rendered: (file) => latest.current.onReportRendered?.(file),
        failed: (message) => latest.current.onError?.(message),
      }),
    }),
  )
  const state = useStoreState(controller.store)
  const filename = props.filename ?? ''
  const data = props.data ?? null
  useEffect(() => {
    void controller.load()
  }, [controller, props.port])
  useEffect(() => controller.setFilename(filename), [controller, filename])
  const first = useRef(true)
  useEffect(() => {
    if (first.current) first.current = false
    else controller.dataChanged()
  }, [controller, data])
  return { t, locale, controller, state, hasData: data !== null }
}
