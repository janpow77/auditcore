/** Typen der Vorlagen-Endpunkte von `reporting_ui/1` (`docs/ui/reporting-rest.md`, auditcore_reporting.web). */
import type { DownloadFile } from '@auditcore/common'

export type TemplateFormat = 'docx' | 'pdf' | 'html'
/** Daten gemäß Datenvertrag (JSON-Schema) der Vorlage. */
export type TemplateData = Readonly<Record<string, unknown>>

export interface TemplateSummary {
  id: string
  version: string
  /** Anzeigename ohne Platzhalter. */
  title: string
  /** Dokumenttitel mit Platzhaltern, z. B. `Prüfbericht {{ aktenzeichen }}`. */
  document_title: string
  description: string
  status: string
  /** `structured` (Blöcke: DOCX, PDF, HTML) oder `docx` (Word-Vorlage: DOCX). */
  kind: 'structured' | 'docx'
  formats: readonly TemplateFormat[]
  fingerprint: string
  versions: readonly string[]
}

export interface DesignProfileInfo {
  id: string
  version: string
  label: string
}

export interface TemplateCatalogue {
  contract: string
  templates: readonly TemplateSummary[]
  designs: readonly DesignProfileInfo[]
  /** Auf dem Server verfügbare Formate (`pdf` braucht das Extra `pdf`). */
  formats: Readonly<Record<TemplateFormat, boolean>>
}

export interface TemplateTextBlock {
  id: string
  title: string
  text: string
  required: boolean
  legal_basis: string
  condition: unknown
}

/** JSON-Schema-Teilmenge des Datenvertrags. */
export interface TemplateSchema {
  type?: string | readonly string[]
  title?: string
  description?: string
  required?: readonly string[]
  properties?: Readonly<Record<string, TemplateSchema>>
  items?: TemplateSchema
  format?: string
  enum?: readonly unknown[]
}

export interface TemplateDetail extends TemplateSummary {
  contract: string
  schema: TemplateSchema
  sample: TemplateData
  conditions: Readonly<Record<string, unknown>>
  text_blocks: readonly TemplateTextBlock[]
}

export interface DataIssue {
  /** JSON-Pfad, z. B. `$.feststellungen[0].betrag`. */
  path: string
  message: string
}

export interface TemplatePreview {
  contract: string
  template: { id: string; version: string; fingerprint: string }
  valid: boolean
  issues: readonly DataIssue[]
  /** Vollständige HTML-Seite ohne Skripte (Anzeige im abgeschotteten iframe). */
  html: string | null
  text_blocks: readonly string[]
  data_sha256: string | null
}

export interface TemplateRequest {
  data: TemplateData
  version?: string
  design?: string
}

export interface TemplateRenderRequest extends TemplateRequest {
  format: TemplateFormat
  filename?: string
}

/** Fachlogik hinter der Oberfläche; Standardumsetzung: `createReportTemplatesRestPort`. */
export interface ReporttemplatesPort {
  templates: () => Promise<TemplateCatalogue>
  template: (id: string, version?: string) => Promise<TemplateDetail>
  preview: (id: string, request: TemplateRequest) => Promise<TemplatePreview>
  render: (id: string, request: TemplateRenderRequest) => Promise<DownloadFile>
}
