/** Typen des REST-Vertrags `documents_extraction/1` (`docs/ui/extraction-rest.md`, auditcore_documents.web). */

export interface ExtractionProfile {
  id: string
  version: string
  fingerprint: string
  label: string
  status: string
  ocr_backend: string | null
  recommended: boolean
  min_field_confidence: number | null
  available: boolean
  retention_categories: readonly string[]
}

export interface ExtractionCatalogue {
  contract: string
  library: string
  enabled: boolean
  engines: Readonly<Record<'router' | 'chandra' | 'tesseract' | 'donut', boolean>>
  profiles: readonly ExtractionProfile[]
  default_profile: string | null
  accepted_types: readonly string[]
  limits: { max_upload_bytes: number }
  thresholds: { ok: number; review: number }
  retention: { stored: boolean; days: Readonly<Record<string, number>> }
}

export type ExtractionRunStatus = 'queued' | 'running' | 'ok' | 'review_needed' | 'rejected' | 'failed' | (string & {})
export type ExtractionOcrQuality = 'ok' | 'review' | 'rejected'
export type ExtractionFieldDecision = 'accepted' | 'rejected' | 'unconfirmed' | 'not_taken' | (string & {})
export type ExtractionJson = string | number | boolean | null | readonly ExtractionJson[] | { readonly [key: string]: ExtractionJson }

export interface ExtractedField {
  name: string
  value: ExtractionJson
  raw: ExtractionJson
  /** Feldkonfidenz des Donut-Modells; `null` ohne Donut. */
  confidence: number | null
  decision: ExtractionFieldDecision | null
  proposal: ExtractionJson
  text_match: boolean | null
  checks: readonly ExtractionJson[]
}

export interface ExtractionFinding {
  rule_id: string
  rule_name: string
  severity: 'INFO' | 'WARN' | 'CRITICAL'
  outcome: 'PASS' | 'FAIL' | 'REVIEW'
  message: string
  evidence: ExtractionJson
}

export interface ExtractionOcrSummary {
  engine: string
  avg_confidence: number
  min_confidence: number
  max_confidence: number
  pages_processed: number
  pages_failed: number
  duration_ms: number
  retries: number
  quality: ExtractionOcrQuality
}

export interface ExtractionRun {
  contract: string
  library: string
  profile: { id: string; version: string; fingerprint: string; status: string }
  run: {
    run_id: string
    status: ExtractionRunStatus
    needs_review: boolean
    error_code: string | null
    error: string | null
    retryable: boolean
    completed_stages: readonly string[]
    hash_chain: readonly string[]
    duration_ms: number | null
  }
  document: {
    filename: string
    sha256: string
    size_bytes: number | null
    mime_type: string | null
    page_count: number | null
  }
  ocr: ExtractionOcrSummary | null
  pages: readonly { page: number; confidence: number | null; text: string }[]
  fields: readonly ExtractedField[]
  findings: readonly ExtractionFinding[]
  flags: readonly string[]
  stored: boolean
}

/**
 * Schnittstelle der Komponente zur Fachlogik; Standardumsetzung:
 * `createExtractionRestPort`. Die Oberfläche erkennt nichts selbst.
 */
export interface ExtractionPort {
  catalogue(): Promise<ExtractionCatalogue>
  run(file: Blob, filename: string, profile: string): Promise<ExtractionRun>
}
