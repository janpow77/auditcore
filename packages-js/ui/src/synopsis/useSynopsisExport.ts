import type { Ref } from 'vue'
import { buildSynopsisExport, deliverExport, type ClientExportFormat, type ExportPayload, type SynopsisSelection, type SynopsisTranslate } from '@flowaudit/ui-core'

export { downloadText, printHtml } from '@flowaudit/ui-core'

export interface UseSynopsisExport {
  build: (format: ClientExportFormat) => ExportPayload | null
  run: (format: ClientExportFormat) => ExportPayload | null
}

/** Exporte der sichtbaren, ausgewählten Zeilen; `onExport` erhält jedes Ergebnis. */
export function useSynopsisExport(
  selection: Readonly<Ref<SynopsisSelection>>,
  t: SynopsisTranslate,
  locale: Readonly<Ref<string>>,
  onExport: (payload: ExportPayload) => void,
): UseSynopsisExport {
  const build = (format: ClientExportFormat): ExportPayload | null => buildSynopsisExport(selection.value, format, t, locale.value)

  function run(format: ClientExportFormat): ExportPayload | null {
    const payload = build(format)
    if (!payload) return null
    onExport(payload)
    deliverExport(payload)
    return payload
  }

  return { build, run }
}
