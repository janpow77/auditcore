/**
 * Choices of the export dialog (extends `exportTypen.ts` of the
 * audit_designer by CSV process table, risk-control matrix, findings list,
 * neutral mode, page format and header).
 */

import type { Orientation } from '../layout/pageFormats'

export type ExportFormat =
  | 'svg'
  | 'png'
  | 'pdf'
  | 'bpmn'
  | 'myst'
  | 'prozesstabelle-csv'
  | 'prozesstabelle-myst'
  | 'rcm-csv'
  | 'feststellungen-csv'
  | 'excel'

export interface ExportChoice {
  format: ExportFormat
  /** Document title, above the diagram. */
  title: string
  subtitle: string
  showHeader: boolean
  showLegend: boolean
  showMarkerLegend: boolean
  showMetadata: boolean
  showLegalBases: boolean
  /** Neutralise before export (bodies, persons, findings). */
  neutral: boolean
  pageFormat: 'a4' | 'a3'
  orientation: Orientation | 'auto'
}

export const DEFAULT_EXPORT_CHOICE: Omit<ExportChoice, 'format'> = {
  title: '',
  subtitle: '',
  showHeader: true,
  showLegend: true,
  showMarkerLegend: true,
  showMetadata: true,
  showLegalBases: true,
  neutral: false,
  pageFormat: 'a4',
  orientation: 'auto',
}
