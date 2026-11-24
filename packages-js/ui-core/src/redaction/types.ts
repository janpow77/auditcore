/** Typen des REST-Vertrags `pdf_redaction/1` (`docs/ui/redaction-rest.md`, auditcore_pdf.web). */

/** Rechteck `[x0, y0, x1, y1]`, Anzeigekoordinaten 0…1 bezogen auf die gedrehte Seite. */
export type RedactionBox = readonly [number, number, number, number]

export interface RedactionPatternInfo {
  id: string
  label: string
  hint: string
  /** KI-basiert (Namenserkennung) statt fester Ausdruck. */
  ai: boolean
  /** `false`, wenn die Anwendung keine KI-Namenserkennung angeschlossen hat. */
  available: boolean
}

export interface RedactionLimits {
  max_upload_bytes: number
  max_pages: number
  max_selection_bytes: number
  max_terms: number
  max_term_length: number
  max_areas: number
  max_areas_per_page: number
}

export interface RedactionCatalogue {
  contract: string
  library: string
  ner_available: boolean
  patterns: readonly RedactionPatternInfo[]
  limits: RedactionLimits
}

export interface RedactionCriteria {
  patterns: readonly string[]
  terms: readonly string[]
  case_sensitive: boolean
  whole_word: boolean
}

export interface RedactionCandidate {
  id: string
  kind: 'text' | 'hidden'
  source: string
  label: string
  text: string
  page: number | null
  /** Anzeigekoordinaten je Zeile. */
  rects: readonly RedactionBox[]
  pdf_rect: RedactionBox | null
  location: string
  outside_view: boolean
  selected: boolean
}

export interface RedactionPageInfo {
  page: number
  width: number
  height: number
  rotation: number
  has_text: boolean
}

/** Plan der Schwärzung; enthält Klartext der Fundstellen und bleibt nur im Arbeitsspeicher. */
export interface RedactionPlan {
  contract: string
  version: number
  sha256: string
  criteria: RedactionCriteria
  page_count: number
  pages: readonly RedactionPageInfo[]
  pages_without_text: readonly number[]
  total: number
  by_source: Readonly<Record<string, number>>
  candidates: readonly RedactionCandidate[]
  cleanup: { metadata_fields: readonly string[]; xmp: boolean; attachments: number; javascript: boolean }
}

/** Eigener Bereich (z. B. Unterschrift, Bild); `id` vergibt die Oberfläche. */
export interface RedactionArea {
  id: string
  page: number
  rect: RedactionBox
}

/** Bestätigte Auswahl für `POST /apply`. */
export interface RedactionSelection {
  sha256: string
  criteria: RedactionCriteria
  selected: string[]
  areas: { page: number; rect: [number, number, number, number] }[]
  sanitize: boolean
}

/** Zahlen des nachgeprüften Berichts aus den Antwortköpfen (ohne Klartext). */
export interface RedactionReport {
  redactions: number
  areas: number
  hidden: number
  deselected: number
  pages: number
  sanitized: boolean
  verified: boolean
}

export interface RedactionResult {
  blob: Blob
  filename: string
  report: RedactionReport
}

/**
 * Schnittstelle der Komponente zur Fachlogik; Standardumsetzung:
 * `createRedactionRestPort`. Jede Anfrage trägt die Datei erneut, der
 * Dienst speichert nichts.
 */
export interface RedactionPort {
  catalogue(): Promise<RedactionCatalogue>
  plan(file: Blob, filename: string, criteria: RedactionCriteria): Promise<RedactionPlan>
  /** Bild (PNG) einer Seite, 1-basiert. */
  preview(file: Blob, filename: string, page: number): Promise<Blob>
  apply(file: Blob, filename: string, selection: RedactionSelection): Promise<RedactionResult>
}
