/**
 * Port mit den Antworten des echten Python-Backends (Fixtures von
 * auditcore_reporting.web, synthetische Vorhaben). `calls` hält die Anfragen
 * fest; `failing` lässt eine Methode scheitern.
 */
import type { ReportingCatalogue, ReportingPort, ReportTableInput, WorkbookPreview, WorkbookRequest } from '../../src'
import profiles from '../fixtures/reporting-profiles.json'
import previewResult from '../fixtures/reporting-preview.json'
import tables from '../fixtures/reporting-tables.json'

export const reportingCatalogue = profiles as unknown as ReportingCatalogue
export const reportingPreview = previewResult as unknown as WorkbookPreview
export const reportingTables = tables as unknown as readonly ReportTableInput[]

export type ReportingFake = ReportingPort & { calls: Record<'preview' | 'export', WorkbookRequest[]> }

export function fakeReportingPort(failing?: keyof ReportingPort, options: { excel?: boolean } = {}): ReportingFake {
  const calls: ReportingFake['calls'] = { preview: [], export: [] }
  const fail = (name: keyof ReportingPort): void => {
    if (failing === name) throw new Error('Dienst nicht erreichbar')
  }
  const catalogue = { ...reportingCatalogue, excel_available: options.excel ?? true }
  return {
    calls,
    profiles: async () => (fail('profiles'), catalogue),
    preview: async (request) => (fail('preview'), calls.preview.push(request), reportingPreview),
    exportWorkbook: async (request) => {
      fail('exportWorkbook')
      calls.export.push(request)
      const filename = `${request.filename ?? 'bericht'}.xlsx`
      return { blob: new Blob(['PK']), filename, mediaType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' }
    },
  }
}
