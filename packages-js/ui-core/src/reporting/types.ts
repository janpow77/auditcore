/** Typen des REST-Vertrags `reporting_ui/1` (`docs/ui/reporting-rest.md`, auditcore_reporting.web). */
import type { DownloadFile } from '@flowaudit/common'

/** Spaltentyp: `json` übernimmt den JSON-Typ wie gesendet; `date`/`datetime` erwarten ISO-Text. */
export type ReportColumnType = 'json' | 'text' | 'number' | 'boolean' | 'date' | 'datetime'
export type ReportCell = string | number | boolean | null

/** Eine Tabelle (ein Blatt) der Anwendung; Zeilen in Spaltenreihenfolge. */
export interface ReportTableInput {
  name: string
  columns: readonly string[]
  rows: readonly (readonly ReportCell[])[]
  types?: Readonly<Record<string, ReportColumnType>>
  /** Ausdrückliche Excel-Formate je Spalte (z. B. `"@"` für Kennungen). */
  formats?: Readonly<Record<string, string>>
}

export interface FormatProfile {
  id: string
  label: string
  description: string
  version: string
  status: string
  /** Herkunft: `repository@commit` oder Art des Profils. */
  source: string | null
}

export interface ReportingCatalogue {
  contract: string
  library: string
  excel_available: boolean
  profiles: readonly FormatProfile[]
  column_types: readonly ReportColumnType[]
  limits: {
    max_rows_per_sheet: number
    max_columns: number
    max_sheets: number
    max_cells: number
    max_text_characters: number
    max_output_bytes: number
    max_body_bytes: number
    sample_rows: number
  }
}

export interface WorkbookRequest {
  profile: string
  tables: readonly ReportTableInput[]
  filename?: string
}

export interface ColumnPreview {
  name: string
  type: ReportColumnType
  format: string
  source: 'profile' | 'override'
}

export interface TablePreview {
  name: string
  rows: number
  columns: readonly ColumnPreview[]
  sample: readonly (readonly ReportCell[])[]
}

export interface WorkbookPreview {
  contract: string
  profile: string
  tables: readonly TablePreview[]
  /** Probelauf des Exports; `null`, wenn das Extra `excel` fehlt. */
  workbook: { bytes: number; filename: string } | null
}

/** Schnittstelle der Komponente zur Fachlogik; Standardumsetzung: `createReportingRestPort`. */
export interface ReportingPort {
  profiles(): Promise<ReportingCatalogue>
  preview(request: WorkbookRequest): Promise<WorkbookPreview>
  exportWorkbook(request: WorkbookRequest): Promise<DownloadFile>
}
