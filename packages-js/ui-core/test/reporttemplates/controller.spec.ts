import { describe, expect, it } from 'vitest'
import {
  buildTemplateRequest,
  createReporttemplatesController,
  createReportTemplatesRestPort,
  formatOptions,
  reporttemplatesCanRender,
  reporttemplatesIsEmpty,
  schemaFields,
  textBlockRows,
  type ReporttemplatesPort,
  type TemplateData,
} from '../../src'
import { fakeTemplatesPort, templateDetails } from './fake-port'

function controller(port: ReporttemplatesPort | null = fakeTemplatesPort(), data: TemplateData | null = null) {
  const events: string[] = []
  const created = createReporttemplatesController({
    port: () => port,
    data: () => data,
    callbacks: () => ({
      selected: (detail) => events.push(`selected:${detail.id}`),
      previewed: (result) => events.push(`previewed:${result.valid}`),
      rendered: (file) => events.push(`rendered:${file.filename}`),
      failed: (message) => events.push(`failed:${message}`),
    }),
  })
  return { created, events }
}

describe('createReporttemplatesController', () => {
  it('lädt Vorlagen, wählt die erste und ihren Datenvertrag', async () => {
    const { created, events } = controller()
    await created.load()
    const state = created.store.get()
    expect(state.templateId).toBe('pruefbericht')
    expect(state.format).toBe('docx')
    expect(state.designId).toBe('neutral-v1')
    expect(events).toEqual(['selected:pruefbericht'])
    expect(schemaFields(state.detail).find((row) => row.name === 'feststellungen')?.type).toBe('Liste von object')
    expect(textBlockRows(state.detail)[0]).toMatchObject({ id: 'rechtsgrundlage', required: true, legalBasis: 'Art. 77 VO (EU) 2021/1060' })
  })

  it('Vorschau mit Beispieldaten, ungültige Daten der Anwendung', async () => {
    const port = fakeTemplatesPort()
    const { created, events } = controller(port, { aktenzeichen: 'X' })
    await created.load()
    await created.preview()
    expect(created.store.get().preview?.valid).toBe(false)
    expect(port.calls.preview[0]).toEqual(['pruefbericht', { data: { aktenzeichen: 'X' }, version: '1.0.0', design: 'neutral-v1' }])
    const sample = controller(fakeTemplatesPort())
    await sample.created.load()
    await sample.created.preview()
    expect(sample.created.store.get().preview?.valid).toBe(true)
    expect(events).toContain('previewed:false')
  })

  it('Vorschau veraltet bei Gestaltung oder Daten; Bericht mit Format und Dateiname', async () => {
    const port = fakeTemplatesPort()
    const { created, events } = controller(port)
    await created.load()
    await created.preview()
    created.setDesign('neutral-v1')
    created.dataChanged()
    expect(created.store.get().stale).toBe(true)
    created.setFormat('pdf')
    created.setFilename(' Bericht ')
    const file = await created.render()
    expect(file?.filename).toBe('Bericht.pdf')
    expect(port.calls.render[0]?.[1]).toMatchObject({ format: 'pdf', filename: 'Bericht' })
    expect(created.store.get().renderedName).toBe('Bericht.pdf')
    expect(events.at(-1)).toBe('rendered:Bericht.pdf')
  })

  it('Format ohne Extra auf dem Server ist nicht erzeugbar', async () => {
    const { created } = controller(fakeTemplatesPort({ pdf: false }))
    await created.load()
    created.setFormat('pdf')
    const state = created.store.get()
    expect(formatOptions(state)).toEqual([{ format: 'docx', available: true }, { format: 'pdf', available: false }, { format: 'html', available: true }])
    expect(reporttemplatesCanRender(state)).toBe(false)
    expect(await created.render()).toBeNull()
  })

  it('meldet Fehler, leere Kataloge und fehlenden Port', async () => {
    const failing = controller(fakeTemplatesPort({ failing: 'template' }))
    await failing.created.load()
    expect(failing.events).toEqual(['failed:Dienst nicht erreichbar'])
    const empty = controller(fakeTemplatesPort({ empty: true }))
    await empty.created.load()
    expect(reporttemplatesIsEmpty(empty.created.store.get())).toBe(true)
    const none = controller(null)
    await none.created.load()
    await none.created.preview()
    expect(none.created.store.get().catalogue).toBeNull()
    expect(buildTemplateRequest(none.created.store.get(), null)).toBeNull()
  })

  it('Vorlagenwahl zurücksetzen und andere Vorlage wählen', async () => {
    const { created } = controller()
    await created.load()
    await created.select(null)
    expect(created.store.get().detail).toBeNull()
    await created.select('vermerk')
    expect(created.store.get().detail?.title).toBe(templateDetails.vermerk?.title)
  })
})

describe('createReportTemplatesRestPort', () => {
  it('ruft die Vorlagen-Endpunkte auf', async () => {
    const seen: string[] = []
    const fetch = async (url: string | URL | Request, init?: RequestInit): Promise<Response> => {
      seen.push(`${init?.method ?? 'GET'} ${String(url)}`)
      if (String(url).endsWith('/render')) return new Response('PK', { headers: { 'Content-Disposition': 'attachment; filename="b.docx"' } })
      return new Response('{}', { headers: { 'Content-Type': 'application/json' } })
    }
    const port = createReportTemplatesRestPort({ baseUrl: '/api/reporting', fetch })
    await port.templates()
    await port.template('prüf bericht', '1.0.0')
    await port.preview('vermerk', { data: {} })
    const file = await port.render('vermerk', { data: {}, format: 'docx' })
    expect(file.filename).toBe('b.docx')
    expect(seen).toEqual([
      'GET /api/reporting/templates',
      'GET /api/reporting/templates/pr%C3%BCf%20bericht?version=1.0.0',
      'POST /api/reporting/templates/vermerk/preview',
      'POST /api/reporting/templates/vermerk/render',
    ])
  })
})
