import type { ComputedRef } from 'vue'
import { saveFile } from '../rest/download'
import { exportFilename, toHtml, toMarkdown } from './exporters'
import type { ClientExportFormat, ExportPayload } from './types'
import type { RowView, SynopsisTranslate, SynopsisView } from './viewModel'

/** Text als Datei anbieten (Blob-URL); ohne Blob-Unterstützung geschieht nichts. */
export function downloadText(content: string, filename: string, mimeType: string): boolean {
  if (typeof URL.createObjectURL !== 'function') return false
  saveFile({ blob: new Blob([content], { type: mimeType }), filename, mediaType: mimeType })
  return true
}

/**
 * Druckansicht in einem unsichtbaren Rahmen öffnen („Als PDF speichern“ im
 * Druckdialog). Kein Pop-up, daher auch mit Pop-up-Blocker nutzbar.
 */
export function printHtml(html: string): HTMLIFrameElement {
  const frame = document.createElement('iframe')
  frame.setAttribute('aria-hidden', 'true')
  frame.tabIndex = -1
  frame.style.cssText = 'position:fixed;width:0;height:0;border:0;right:0;bottom:0'
  frame.addEventListener('load', () => {
    const target = frame.contentWindow
    if (!target) return
    target.addEventListener('afterprint', () => frame.remove())
    target.focus()
    target.print()
  })
  frame.srcdoc = html
  document.body.append(frame)
  return frame
}

export interface UseSynopsisExport {
  build: (format: ClientExportFormat) => ExportPayload | null
  run: (format: ClientExportFormat) => ExportPayload | null
}

/** Exporte der sichtbaren, ausgewählten Zeilen; `onExport` erhält jedes Ergebnis. */
export function useSynopsisExport(
  view: ComputedRef<SynopsisView | null>,
  rows: ComputedRef<RowView[]>,
  t: SynopsisTranslate,
  locale: ComputedRef<string>,
  onExport: (payload: ExportPayload) => void,
): UseSynopsisExport {
  function build(format: ClientExportFormat): ExportPayload | null {
    const current = view.value
    if (!current) return null
    const input = { view: current, rows: rows.value, t, lang: locale.value }
    if (format === 'markdown') {
      return { format, filename: exportFilename(current.title, 'md'), mimeType: 'text/markdown;charset=utf-8', content: toMarkdown(input) }
    }
    return { format, filename: exportFilename(current.title, 'html'), mimeType: 'text/html;charset=utf-8', content: toHtml(input) }
  }

  function run(format: ClientExportFormat): ExportPayload | null {
    const payload = build(format)
    if (!payload) return null
    onExport(payload)
    if (format === 'print') printHtml(payload.content)
    else downloadText(payload.content, payload.filename, payload.mimeType)
    return payload
  }

  return { build, run }
}
