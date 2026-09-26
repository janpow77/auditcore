/**
 * REST-Vertrag `documents_batch_checks/1` von `auditcore_documents.web`
 * (Bestandsprüfung über viele Belege, `docs/ui/batch-checks-rest.md`).
 */
import type { DownloadFile } from '@auditcore/common'

export type BatchchecksLevel = 'info' | 'warning' | 'blocker'
export type BatchchecksRuleStatus = 'passed' | 'findings' | 'not_checked' | 'result'
export type BatchchecksScope = 'document' | 'inventory' | 'run'
export type BatchchecksExportFormat = 'json' | 'csv'

/** Prüfregel des Katalogs: was geprüft wird, Rechtsgrundlage, Herkunft. */
export interface BatchchecksRule {
  code: string
  title: string
  checks: string
  legal_basis: string
  scope: BatchchecksScope
  source: string
}

/** Feld des Bestands mit Spaltennamen für die automatische Zuordnung. */
export interface BatchchecksField {
  name: string
  label: string
  aliases: readonly string[]
  numeric: boolean
}

export interface BatchchecksOptions {
  total_volume: number | null
  tolerance: number
  concentration_threshold: number
  block_threshold: number
  supplementary: boolean
}

export interface BatchchecksCatalogue {
  contract: string
  library: string
  rules: readonly BatchchecksRule[]
  fields: readonly BatchchecksField[]
  defaults: BatchchecksOptions
  levels: readonly { id: BatchchecksLevel; label: string }[]
  limits: { max_documents: number; max_body_bytes: number }
  export_formats: readonly BatchchecksExportFormat[]
  stored: boolean
}

/** Beleg der Anfrage: flacher Datensatz oder Lauf der Belegerkennung (`documents_extraction/1`). */
export type BatchchecksDocument = Readonly<Record<string, unknown>>

export interface BatchchecksRequest {
  documents: readonly BatchchecksDocument[]
  options?: Partial<BatchchecksOptions>
}

export interface BatchchecksRuleResult extends BatchchecksRule {
  status: BatchchecksRuleStatus
  note: string | null
  findings: number
  documents: number
  level: BatchchecksLevel | null
}

export interface BatchchecksFinding {
  id: string
  rule: string
  category: string
  level: BatchchecksLevel
  field: string | null
  /** Begründung (deutsch). */
  message: string
  /** Betroffene Belege (0-basiert). */
  documents: readonly number[]
  evidence: Readonly<Record<string, unknown>>
  rule_reference: string
}

export interface BatchchecksDocumentResult {
  index: number
  ref: string
  supplier_name: string | number | null
  invoice_number: string | number | null
  invoice_date: string | number | null
  gross_amount: string | number | null
  ocr_confidence: number | null
  findings: number
  level: BatchchecksLevel | null
  rules: readonly string[]
}

export interface BatchchecksSummary {
  documents: number
  findings: number
  documents_with_findings: number
  escalation_level: BatchchecksLevel
  report_blocked: boolean
  block_reason: string | null
  timestamp: string
}

export interface BatchchecksMetrics {
  total_documents: number
  mandatory_fields_success_rate: number
  per_field_success: Readonly<Record<string, number>>
  documents_with_errors: number
  documents_with_errors_rate: number
  avg_ocr_confidence: number | null
  min_ocr_confidence: number | null
  escalated_documents: number
  formal_correctness_rate: number
}

/** Antwort von `POST /runs`. */
export interface BatchchecksAnswer {
  contract: string
  library: string
  options: BatchchecksOptions
  summary: BatchchecksSummary
  metrics: BatchchecksMetrics
  rules: readonly BatchchecksRuleResult[]
  findings: readonly BatchchecksFinding[]
  documents: readonly BatchchecksDocumentResult[]
  stored: boolean
}

/** Fachlogik hinter der Oberfläche; Vue und React rufen nur diesen Port auf. */
export interface BatchchecksPort {
  catalogue: () => Promise<BatchchecksCatalogue>
  run: (request: BatchchecksRequest) => Promise<BatchchecksAnswer>
  exportRun: (request: BatchchecksRequest, format: BatchchecksExportFormat) => Promise<DownloadFile>
}
