/**
 * JSON-Formen des REST-Vertrags (docs/ui/synopsis-rest.md). Sie entsprechen
 * `ComparisonResult.to_dict()` aus `auditcore_documents`; die Oberfläche kennt
 * keine zweite Datenform.
 */

export type RowStatus = 'changed' | 'removed' | 'added' | 'moved' | 'unchanged'
export const ROW_STATUSES: readonly RowStatus[] = ['changed', 'removed', 'added', 'moved', 'unchanged']
/** Vorgabe des Filters „Alle Änderungen“: alles außer unverändert. */
export const CHANGE_STATUSES: readonly RowStatus[] = ['changed', 'removed', 'added', 'moved']

export type DiffField = 'text' | 'answer' | 'comment' | 'note'

export interface CompareRow {
  row_id: string
  status: RowStatus | string
  location: string
  old_text: string
  new_text: string
  old_answer?: string
  new_answer?: string
  old_comment?: string
  new_comment?: string
  old_note?: string
  new_note?: string
  reason?: string
  /** `''`, `flowagent` (KI-Vorschlag) oder `article_law` (Änderungsbefehl). */
  reason_source?: string
  reason_verified?: boolean | null
  reason_warning?: string
  selected?: boolean
  /** Wortdifferenz im Format von `difflib.ndiff` je Feld. */
  diff?: Partial<Record<DiffField, readonly string[]>>
}

export interface ConsolidatedParagraph {
  section: string
  paragraph: number
  text: string
  repealed: boolean
  inserted: boolean
}

export interface ComparisonMetadata {
  comparison_type?: 'standard' | 'article_law' | string
  detected_mode?: string
  highlight_words?: boolean
  output_sections?: readonly string[]
  pdf_notice?: string
  profile?: { id: string; version: string; fingerprint: string }
  old_label?: string
  new_label?: string
  reason_label?: string
  recognised_commands?: number
  open_commands?: readonly string[]
  open_command_count?: number
  consolidated_text?: readonly ConsolidatedParagraph[]
  work_aid_notice?: string
  [key: string]: unknown
}

export interface ComparisonResult {
  version: string
  mode: 'checklist' | 'text' | string
  old_filename: string
  new_filename: string
  old_sha256: string
  new_sha256: string
  old_count: number
  new_count: number
  matched_count: number
  changed_count: number
  removed_count: number
  added_count: number
  moved_count?: number
  rows: readonly CompareRow[]
  created_at: string
  metadata?: ComparisonMetadata
}

/** Ein gespeicherter Vergleich (`GET /comparisons/{id}`). */
export interface Comparison {
  id: string
  title: string
  created_at: string
  result: ComparisonResult
}

export interface ComparisonSummary {
  id: string
  title: string
  created_at: string
  old_filename: string
  new_filename: string
  comparison_type: string
  counts: { changed: number; removed: number; added: number; moved: number }
}

export interface ComparisonProfile {
  id: string
  version: string
  fingerprint: string
  status: string
  default: boolean
}

/** Änderung einer Zeile (`PATCH /comparisons/{id}/rows`). */
export interface RowUpdate {
  row_id: string
  selected?: boolean
  reason?: string
}

export type SynopsisLayout = 'side-by-side' | 'inline'
export type ClientExportFormat = 'html' | 'markdown' | 'print'
export type ServerExportFormat = 'json' | 'markdown' | 'docx' | 'pdf'

/** Ergebnis eines Exports in der Oberfläche (Ereignis `export`). */
export interface ExportPayload {
  format: ClientExportFormat
  filename: string
  mimeType: string
  content: string
}
