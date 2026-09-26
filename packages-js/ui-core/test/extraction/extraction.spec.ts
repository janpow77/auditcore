import { describe, expect, it, vi } from 'vitest'
import {
  createExtractionController,
  createExtractionRestPort,
  extractionAccept,
  extractionConfidenceTone,
  extractionFieldLabel,
  extractionSizeText,
  extractionValidation,
  extractionValueText,
  INITIAL_EXTRACTION,
  splitExtractionFindings,
  translator,
  extractionMessages,
} from '../../src'
import { extractionCatalogue, fakeExtractionPort, runDonut, syntheticFile } from './fake-port'

const t = translator(extractionMessages, 'de')

describe('Belegerkennung: Zustandsautomat', () => {
  it('lädt den Katalog und wählt das Standardprofil', async () => {
    const controller = createExtractionController({ port: () => fakeExtractionPort() })
    await controller.load()
    expect(controller.store.get().profileId).toBe('auditcore.pipeline')
  })

  it('verlangt eine Datei, prüft die Größe und sendet Name, Profil und Datei', async () => {
    const port = fakeExtractionPort()
    const completed = vi.fn()
    const controller = createExtractionController({ port: () => port, callbacks: () => ({ completed }) })
    await controller.load()
    await controller.extract()
    expect(controller.store.get().validation).toBe('needFile')
    controller.selectFile(syntheticFile('gross.png', extractionCatalogue.limits.max_upload_bytes + 1))
    await controller.extract()
    expect(controller.store.get().validation).toBe('tooLarge')
    controller.selectFile(syntheticFile())
    controller.setProfile('auditcore.pipeline.donut')
    await controller.extract()
    expect(port.calls).toEqual([['beleg.png', 'auditcore.pipeline.donut', 64]])
    expect(controller.store.get().result).toBe(runDonut)
    expect(completed).toHaveBeenCalledWith(runDonut)
  })

  it('meldet Portfehler und ein nicht verfügbares Profil', async () => {
    const failed = vi.fn()
    const controller = createExtractionController({ port: () => fakeExtractionPort({ failing: 'run' }), callbacks: () => ({ failed }) })
    await controller.load()
    controller.selectFile(syntheticFile())
    await controller.extract()
    expect(controller.store.get().error).toBe('Dienst nicht erreichbar')
    expect(failed).toHaveBeenCalledWith('Dienst nicht erreichbar')
    const unavailable = { ...extractionCatalogue, profiles: extractionCatalogue.profiles.map((p) => ({ ...p, available: false })) }
    expect(extractionValidation({ ...INITIAL_EXTRACTION, catalogue: unavailable, profileId: 'auditcore.pipeline', file: syntheticFile() })).toBe('profile')
  })
})

describe('Belegerkennung: Anzeige', () => {
  it('ordnet auffällige Befunde vor bestandene', () => {
    const split = splitExtractionFindings(runDonut.findings)
    expect(split.open.map((f) => f.outcome)).toEqual(['FAIL', 'REVIEW'])
    expect(split.passed.every((f) => f.outcome === 'PASS')).toBe(true)
  })

  it('beschriftet Felder, Werte, Konfidenzen und Dateitypen', () => {
    expect(extractionFieldLabel('vat_id', t)).toBe('USt-IdNr.')
    expect(extractionFieldLabel('unbekannt', t)).toBe('unbekannt')
    expect(extractionValueText(1234.5, 'de')).toBe('1.234,5')
    expect(extractionValueText(null, 'de')).toBe('')
    expect(extractionConfidenceTone(0.81, 0.9)).toBe('warning')
    expect(extractionConfidenceTone(null, 0.9)).toBe('neutral')
    expect(extractionSizeText(5 * 1024 * 1024, 'de')).toBe('5 MiB')
    expect(extractionAccept(extractionCatalogue)).toContain('.pdf')
  })
})

describe('Belegerkennung: REST-Port', () => {
  it('sendet multipart an /runs und wandelt Fehler in RestError', async () => {
    const fetch = vi.fn(async (url: string, init?: RequestInit) => {
      if (url.endsWith('/profile')) return new Response(JSON.stringify(extractionCatalogue))
      const form = init?.body as FormData
      expect(form.get('profile')).toBe('auditcore.pipeline')
      return new Response(JSON.stringify({ error: { code: 'extraction_disabled', message: 'abgeschaltet' } }), { status: 404 })
    })
    const port = createExtractionRestPort({ baseUrl: '/api/extraction/', fetch })
    expect((await port.catalogue()).contract).toBe('documents_extraction/1')
    await expect(port.run(syntheticFile(), 'beleg.png', 'auditcore.pipeline')).rejects.toMatchObject({ status: 404, code: 'extraction_disabled', message: 'abgeschaltet' })
    expect(fetch.mock.calls[1]?.[0]).toBe('/api/extraction/runs')
  })
})
