/**
 * Browser-Helfer für Exporte (DOM, aber framework-frei): Datei anbieten und
 * Druckansicht öffnen. Vue- und React-Fassung rufen dieselben Funktionen.
 */
import { saveFile } from '@flowaudit/common/browser'

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

/** Export ausliefern: Druckansicht (`print`) oder Datei. */
export function deliverExport(payload: { format: string; content: string; filename: string; mimeType: string }): void {
  if (payload.format === 'print') printHtml(payload.content)
  else downloadText(payload.content, payload.filename, payload.mimeType)
}
