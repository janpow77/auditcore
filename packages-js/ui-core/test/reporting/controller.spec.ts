import { describe, expect, it, vi } from 'vitest'
import { buildWorkbookRequest, createReportingController, createReportingRestPort, INITIAL_REPORTING, reportCellText, reportingSampleNote, reportingTablesText, reportingMessages, translator } from '../../src'
import { fakeReportingPort, reportingPreview, reportingTables } from './fake-port'

const t = translator(reportingMessages, 'de')

describe('Tabellenexport: Zustandsautomat', () => {
  it('lädt Profile, wählt das erste sichtbar vor und fordert die Vorschau an', async () => {
    const port = fakeReportingPort()
    const previewed = vi.fn()
    const controller = createReportingController({ port: () => port, tables: () => reportingTables, callbacks: () => ({ previewed }) })
    await controller.load()
    expect(controller.store.get().profileId).toBe('flowlib-legacy-v1')
    controller.setFilename('  Vorhabenliste ')
    await controller.preview()
    expect(port.calls.preview[0]).toEqual({ profile: 'flowlib-legacy-v1', tables: reportingTables, filename: 'Vorhabenliste' })
    expect(previewed).toHaveBeenCalledWith(reportingPreview)
    controller.setProfile('plain-v1')
    expect(controller.store.get().stale).toBe(true)
  })

  it('prüft Tabellen und Profil vor jeder Anfrage', async () => {
    const port = fakeReportingPort()
    const controller = createReportingController({ port: () => port, tables: () => [] })
    await controller.load()
    await controller.preview()
    expect(controller.store.get().validation).toBe('noTables')
    expect(buildWorkbookRequest({ ...INITIAL_REPORTING, profileId: null }, reportingTables)).toEqual({ ok: false, error: 'profile' })
    expect(port.calls.preview).toHaveLength(0)
  })

  it('exportiert, meldet den Dateinamen und Fehler des Ports', async () => {
    const port = fakeReportingPort()
    const exported = vi.fn()
    const controller = createReportingController({ port: () => port, tables: () => reportingTables, callbacks: () => ({ exported }) })
    await controller.load()
    const file = await controller.exportWorkbook()
    expect(file?.filename).toBe('bericht.xlsx')
    expect(controller.store.get().exportedName).toBe('bericht.xlsx')
    expect(exported).toHaveBeenCalledOnce()
    const failing = createReportingController({ port: () => fakeReportingPort('exportWorkbook'), tables: () => reportingTables })
    await failing.load()
    expect(await failing.exportWorkbook()).toBeNull()
    expect(failing.store.get().error).toBe('Dienst nicht erreichbar')
  })

  it('Anzeige: Zellen, Zusammenfassung, Hinweis bei gekürzter Vorschau', () => {
    expect(reportCellText(null, 'de')).toBe('—')
    expect(reportCellText(1234.5, 'de')).toBe('1.234,5')
    expect(reportingTablesText(reportingTables, t, 'de')).toBe('1 Tabelle(n), 3 Zeilen')
    const table = reportingPreview.tables[0]!
    expect(reportingSampleNote(table, t, 'de')).toBe('')
    expect(reportingSampleNote({ ...table, rows: 50 }, t, 'de')).toBe('Vorschau zeigt 3 von 50 Zeilen.')
  })

  it('REST-Port: Pfade und Dateiname aus Content-Disposition', async () => {
    const fetch = vi.fn(async (url: string) => url.endsWith('/export')
      ? new Response('PK', { headers: { 'Content-Disposition': "attachment; filename=\"Pr_fung.xlsx\"; filename*=UTF-8''Pr%C3%BCfung.xlsx" } })
      : new Response('{}'))
    const port = createReportingRestPort({ baseUrl: '/api/reporting/', fetch })
    await port.profiles()
    await port.preview({ profile: 'plain-v1', tables: reportingTables })
    const file = await port.exportWorkbook({ profile: 'plain-v1', tables: reportingTables })
    expect(fetch.mock.calls.map((call) => call[0])).toEqual(['/api/reporting/profiles', '/api/reporting/preview', '/api/reporting/export'])
    expect(file.filename).toBe('Prüfung.xlsx')
  })
})
