import type { DownloadFile } from '../http/rest'
import { toIsoDate } from '../format/date'

/** Wartezeit bis zur Freigabe der Objekt-URL (manche Browser starten den Download verzögert). */
const REVOKE_DELAY_MS = 1000

/** Bietet eine Datei im Browser zum Speichern an. */
export function saveFile(file: DownloadFile): void {
  const url = URL.createObjectURL(file.blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = file.filename
  anchor.rel = 'noopener'
  document.body.append(anchor)
  anchor.click()
  anchor.remove()
  setTimeout(() => URL.revokeObjectURL(url), REVOKE_DELAY_MS)
}

/** Optionen für `downloadBlob`. */
export interface DownloadOptions {
  /** Datum `JJJJ-MM-TT_` (Berliner Zeit) vor den Dateinamen setzen. */
  datePrefix?: boolean
  /** Bezugszeitpunkt für `datePrefix` (Standard: jetzt). */
  now?: Date
}

/** Blob unter einem Dateinamen speichern, optional mit Datumspräfix. */
export function downloadBlob(blob: Blob, filename: string, options: DownloadOptions = {}): void {
  const prefix = options.datePrefix ? `${toIsoDate(options.now ?? new Date()) ?? ''}_` : ''
  saveFile({ blob, filename: `${prefix}${filename}`, mediaType: blob.type || 'application/octet-stream' })
}
