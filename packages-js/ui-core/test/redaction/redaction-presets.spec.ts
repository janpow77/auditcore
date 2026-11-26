// Vorgaben der Anwendung: bereitgestellte Datei, Startwerte für Begriffe und Muster.
import { describe, expect, it, vi } from 'vitest'
import { createRedactionController, redactionStep, redactionValidation } from '../../src'
import { fakeRedactionPort, fakeUrls, redactionCatalogueWithoutNer, redactionPlan, syntheticPdf } from './fake-port'

describe('Schwärzen: Vorgaben der Anwendung', () => {
  it('übernimmt eine bereitgestellte Datei ohne Dateifeld und behält sie beim Zurücksetzen', async () => {
    const port = fakeRedactionPort()
    const controller = createRedactionController({ port: () => port, urls: fakeUrls() })
    await controller.load()
    const blob = new Blob([new Uint8Array([0x25, 0x50, 0x44, 0x46, 0x2d])], { type: 'application/pdf' })
    controller.provideFile(blob, ' akte.pdf ')
    expect(controller.store.get()).toMatchObject({ file: blob, filename: 'akte.pdf', fileFixed: true })
    controller.setPattern('email', true)
    await controller.plan()
    expect(redactionStep(controller.store.get())).toBe('review')
    expect(port.calls.find((call) => call[0] === 'plan')?.[1]).toBe('akte.pdf')
    // Gleiche Vorgabe erneut: Plan bleibt erhalten.
    controller.provideFile(blob, 'akte.pdf')
    expect(controller.store.get().plan).not.toBeNull()
    controller.reset()
    expect(controller.store.get()).toMatchObject({ file: blob, filename: 'akte.pdf', fileFixed: true, plan: null })
    // Neue Datei: Plan verfällt.
    await controller.plan()
    const other = new Blob([new Uint8Array([0x25, 0x50, 0x44, 0x46, 0x2d, 0x31])], { type: 'application/pdf' })
    controller.provideFile(other)
    expect(controller.store.get()).toMatchObject({ file: other, filename: 'dokument.pdf', plan: null })
    controller.provideFile(null)
    expect(controller.store.get()).toMatchObject({ file: null, filename: '', fileFixed: false })
    expect(redactionValidation(controller.store.get())).toBe('needFile')
  })

  it('hebt die Vorgabe auf, sobald eine eigene Datei gewählt wird; null ohne Vorgabe ändert nichts', async () => {
    const controller = createRedactionController({ port: () => fakeRedactionPort(), urls: fakeUrls() })
    await controller.load()
    controller.selectFile(syntheticPdf('eigen.pdf'))
    controller.provideFile(null)
    expect(controller.store.get()).toMatchObject({ filename: 'eigen.pdf', fileFixed: false })
    controller.provideFile(new Blob(['%PDF-']), 'akte.pdf')
    controller.selectFile(syntheticPdf('eigen.pdf'))
    expect(controller.store.get()).toMatchObject({ filename: 'eigen.pdf', fileFixed: false })
    controller.reset()
    expect(controller.store.get().file).toBeNull()
  })

  it('belegt Begriffe und Muster vor; unbekannte und nicht verfügbare Muster entfallen', async () => {
    const early = createRedactionController({ port: () => fakeRedactionPort({ catalogue: redactionCatalogueWithoutNer }), urls: fakeUrls() })
    early.presetCriteria({ terms: [' Erika Mustermann ', '', 'Erika Mustermann', 'Musterstraße 1'], patterns: ['iban', 'ki_namen', 'gibt_es_nicht'] })
    expect(early.store.get().terms).toBe('Erika Mustermann\nMusterstraße 1')
    await early.load()
    expect(early.store.get().patterns).toEqual(['iban'])
    early.presetCriteria({ patterns: ['email', 'ki_namen'] })
    expect(early.store.get()).toMatchObject({ patterns: ['email'], terms: 'Erika Mustermann\nMusterstraße 1' })
    early.setTerms('eigener Begriff')
    early.presetCriteria({})
    expect(early.store.get().terms).toBe('eigener Begriff')
  })

  it('verwirft Fehler und Textauszüge des alten Dokuments beim Wechsel der Vorgabe', async () => {
    let reject: (error: Error) => void = () => undefined
    const port = { ...fakeRedactionPort(), apply: () => new Promise<never>((_resolve, fail) => { reject = fail }) }
    const failed = vi.fn()
    const controller = createRedactionController({ port: () => port, urls: fakeUrls(), callbacks: () => ({ failed }) })
    await controller.load()
    const akteA = new Blob(['%PDF-A'], { type: 'application/pdf' })
    controller.provideFile(akteA, 'a.pdf')
    controller.setPattern('email', true)
    await controller.plan()
    const running = controller.apply()
    const akteB = new Blob(['%PDF-B'], { type: 'application/pdf' })
    controller.provideFile(akteB, 'b.pdf')
    reject(new Error('Textauszug aus Akte A'))
    await running
    expect(controller.store.get()).toMatchObject({ filename: 'b.pdf', error: null, busy: null })
    expect(failed).not.toHaveBeenCalled()

    // Ohne Wettlauf: ein Fehler zu A verschwindet beim Wechsel auf B.
    controller.provideFile(akteA, 'a.pdf')
    controller.store.set({ error: 'Fehler zu A' })
    controller.provideFile(akteB, 'b.pdf')
    expect(controller.store.get().error).toBeNull()
  })

  it('verwirft einen Plan zu alten Kriterien und merkt Vorgaben während des Schwärzens und im Ergebnis vor', async () => {
    const port = fakeRedactionPort()
    const controller = createRedactionController({ port: () => port, urls: fakeUrls() })
    await controller.load()
    controller.provideFile(new Blob(['%PDF-']), 'akte.pdf')
    controller.setPattern('email', true)

    // Vorschlag kommt, während der Plan noch läuft: Plan verfällt, Formular zeigt die Vorgabe.
    const planning = controller.plan()
    controller.presetCriteria({ terms: ['Erika Mustermann'] })
    await planning
    expect(controller.store.get()).toMatchObject({ plan: null, terms: 'Erika Mustermann', busy: null })

    // In der Prüfansicht: Plan verfällt ebenso.
    await controller.plan()
    expect(controller.store.get().plan).not.toBeNull()
    controller.presetCriteria({ patterns: ['iban'] })
    expect(controller.store.get()).toMatchObject({ plan: null, patterns: ['iban'] })

    // Während des Schwärzens vorgemerkt, im Ergebnis weiter vorgemerkt, bei „Neu beginnen“ übernommen.
    await controller.plan()
    const applying = controller.apply()
    controller.presetCriteria({ terms: ['Musterstraße 1'] })
    expect(controller.store.get().terms).toBe('Erika Mustermann')
    await applying
    expect(controller.store.get().result).not.toBeNull()
    expect(controller.store.get().terms).toBe('Erika Mustermann')
    controller.reset()
    expect(controller.store.get()).toMatchObject({ terms: 'Musterstraße 1', plan: null, result: null, fileFixed: true })
  })

  it('übernimmt nach fehlgeschlagenem Schwärzen vorgemerkte Vorgaben', async () => {
    const port = fakeRedactionPort({ failing: 'apply' })
    const controller = createRedactionController({ port: () => port, urls: fakeUrls() })
    await controller.load()
    controller.provideFile(new Blob(['%PDF-']), 'akte.pdf')
    controller.setPattern('email', true)
    await controller.plan()
    const applying = controller.apply()
    controller.presetCriteria({ terms: ['Erika Mustermann'] })
    await applying
    expect(controller.store.get()).toMatchObject({ terms: 'Erika Mustermann', plan: null, error: 'Dienst nicht erreichbar' })
  })

  it('übergeht Vorgaben, die keine Listen sind (HTML-Attribut statt Eigenschaft)', async () => {
    const controller = createRedactionController({ port: () => fakeRedactionPort(), urls: fakeUrls() })
    await controller.load()
    controller.setTerms('eigener Begriff')
    controller.presetCriteria({ terms: 'Erika' as unknown as string[], patterns: 'iban' as unknown as string[] })
    expect(controller.store.get()).toMatchObject({ terms: 'eigener Begriff', patterns: [] })
  })

  it('verwirft den Fehler eines veralteten Plans und einen Plan zu inzwischen geänderten Kriterien', async () => {
    let reject: (error: Error) => void = () => undefined
    let resolve: (plan: typeof redactionPlan) => void = () => undefined
    let mode: 'reject' | 'resolve' = 'reject'
    const base = fakeRedactionPort()
    const port = { ...base, plan: () => new Promise<typeof redactionPlan>((ok, fail) => { if (mode === 'reject') reject = fail; else resolve = ok }) }
    const failed = vi.fn()
    const controller = createRedactionController({ port: () => port, urls: fakeUrls(), callbacks: () => ({ failed }) })
    await controller.load()
    controller.provideFile(new Blob(['%PDF-A']), 'a.pdf')
    controller.setPattern('email', true)
    const first = controller.plan()
    controller.provideFile(new Blob(['%PDF-B']), 'b.pdf')
    reject(new Error('Textauszug aus Akte A'))
    await first
    expect(controller.store.get()).toMatchObject({ filename: 'b.pdf', error: null, plan: null })
    expect(failed).not.toHaveBeenCalled()

    mode = 'resolve'
    const second = controller.plan()
    controller.setTerms('nachträglich eingegeben')
    resolve(redactionPlan)
    await second
    expect(controller.store.get()).toMatchObject({ plan: null, terms: 'nachträglich eingegeben', criteriaNotice: 'edited' })
  })

  it('merkt nur gesetzte Schlüssel vor und meldet den verworfenen Plan nach „Auswahl ändern“', async () => {
    let finish: () => void = () => undefined
    const base = fakeRedactionPort()
    const port = { ...base, apply: (file: Blob, filename: string, selection: Parameters<typeof base.apply>[2]) => new Promise<Awaited<ReturnType<typeof base.apply>>>((ok) => { finish = () => void base.apply(file, filename, selection).then(ok) }) }
    const controller = createRedactionController({ port: () => port, urls: fakeUrls() })
    await controller.load()
    controller.provideFile(new Blob(['%PDF-']), 'akte.pdf')
    controller.setPattern('email', true)
    await controller.plan()
    const applying = controller.apply()
    controller.presetCriteria({ terms: ['A'] })
    controller.presetCriteria({ terms: undefined, patterns: ['iban'] })
    finish()
    await applying
    expect(controller.store.get().result).not.toBeNull()
    controller.editAgain()
    expect(controller.store.get()).toMatchObject({ terms: 'A', patterns: ['iban'], plan: null, areas: [], criteriaNotice: 'presets' })
    expect(redactionStep(controller.store.get())).toBe('form')
    await controller.plan()
    expect(controller.store.get().criteriaNotice).toBeNull()
  })

  it('übernimmt vorgemerkte Vorgaben, wenn während des Schwärzens die Datei wechselt', async () => {
    let finish: () => void = () => undefined
    const base = fakeRedactionPort()
    const port = { ...base, apply: (file: Blob, filename: string, selection: Parameters<typeof base.apply>[2]) => new Promise<Awaited<ReturnType<typeof base.apply>>>((ok) => { finish = () => void base.apply(file, filename, selection).then(ok) }) }
    const controller = createRedactionController({ port: () => port, urls: fakeUrls() })
    await controller.load()
    controller.provideFile(new Blob(['%PDF-A']), 'a.pdf')
    controller.setPattern('email', true)
    await controller.plan()
    const applying = controller.apply()
    controller.provideFile(new Blob(['%PDF-B']), 'b.pdf')
    controller.presetCriteria({ terms: ['Erika Mustermann'] })
    finish()
    await applying
    expect(controller.store.get()).toMatchObject({ filename: 'b.pdf', terms: 'Erika Mustermann', result: null, plan: null, busy: null })
  })
})
