import { describe, expect, it, vi } from 'vitest'
import {
  createRedactionController,
  defaultRedactionBox,
  formatRedactionPages,
  isRedactionArrow,
  nudgeRedactionBox,
  redactionBoxFromPoints,
  redactionBoxStyle,
  redactionGroups,
  redactionHiddenLocations,
  redactionMessages,
  redactionPatternText,
  redactionReportRows,
  redactionReview,
  redactionSelectionPayload,
  redactionSizeText,
  redactionStep,
  redactionTerms,
  redactionValidation,
  redactionValidationText,
  resizeRedactionBox,
  translator,
  INITIAL_REDACTION,
  type RedactionData,
} from '../../src'
import { fakeRedactionPort, fakeUrls, redactionCatalogue, redactionCatalogueWithoutNer, redactionPlan, syntheticPdf } from './fake-port'

const t = translator(redactionMessages, 'de')

async function setup(port = fakeRedactionPort(), urls = fakeUrls()) {
  const planned = vi.fn()
  const completed = vi.fn()
  const controller = createRedactionController({ port: () => port, urls, callbacks: () => ({ planned, completed }) })
  await controller.load()
  controller.selectFile(syntheticPdf())
  controller.setPattern('email', true)
  controller.setTerms('Prüfvermerk\n\n Prüfvermerk \n')
  await controller.plan()
  return { controller, port, urls, planned, completed }
}

describe('Schwärzen: Modell', () => {
  it('gruppiert gleiche Fundtexte je Quelle und sortiert nach Häufigkeit', () => {
    const groups = redactionGroups(redactionPlan.candidates)
    expect(groups.map((group) => [group.text, group.items.length, group.pages, group.hidden])).toEqual([
      ['max.muster@beispiel-firma.example', 3, [1, 2], true],
      ['Erika Beispiel', 2, [1], false],
      ['Prüfvermerk', 2, [1], true],
      ['DE89 3704 0044 0532 0130 00', 1, [1], false],
      ['Max Mustermann', 1, [2], false],
    ])
    expect(redactionGroups(redactionPlan.candidates)).toBe(groups)
  })

  it('fasst Seiten zusammen', () => {
    expect(formatRedactionPages([5, 1, 2, 3, 3, 9, 10])).toBe('1–3, 5, 9–10')
    expect(formatRedactionPages([])).toBe('')
  })

  it('liest Begriffe zeilenweise ohne Dubletten', () => {
    expect(redactionTerms(' A \r\nB\n\nA\n')).toEqual(['A', 'B'])
  })

  it('begrenzt Bereiche auf die Seite und hält die Mindestgröße', () => {
    expect(redactionBoxFromPoints([0.8, 1.4], [-1, 0.2])).toEqual([0, 0.2, 0.8, 1])
    expect(resizeRedactionBox([0.2, 0.2, 0.5, 0.5], [0.1, 0.1])).toEqual([0.2, 0.2, 0.204, 0.204])
    expect(nudgeRedactionBox([0.2, 0.2, 0.5, 0.5], 'ArrowRight', 'resize', false)).toEqual([0.2, 0.2, 0.505, 0.5])
    expect(nudgeRedactionBox([0.9, 0.2, 1, 0.5], 'ArrowRight', 'move', true)).toEqual([0.9, 0.2, 1, 0.5])
    expect(nudgeRedactionBox([0.02, 0.2, 0.12, 0.5], 'ArrowLeft', 'move', true)[0]).toBe(0)
    expect(nudgeRedactionBox([0.2, 0.2, 0.3, 0.3], 'ArrowUp', 'move', false)[1]).toBeCloseTo(0.195)
    expect(isRedactionArrow('ArrowUp')).toBe(true)
    expect(isRedactionArrow('Enter')).toBe(false)
    expect(defaultRedactionBox(9)).toEqual([0.33, 0.43, 0.63, 0.51])
    expect(redactionBoxStyle([0.1, 0.2, 0.35, 0.3])).toEqual({ left: '10%', top: '20%', width: '25%', height: '10%' })
  })

  it('nennt versteckte Fundorte ohne Einzelangaben', () => {
    expect(redactionHiddenLocations(redactionPlan)).toBe('Metadaten')
  })

  it('baut die Auswahl in Reihenfolge des Plans', () => {
    const [first, second] = redactionPlan.candidates
    const payload = redactionSelectionPayload(redactionPlan, new Set([second!.id, first!.id, 'fremd']), [{ id: 'x', page: 2, rect: [0, 0, 0.5, 0.5] }], false)
    expect(payload).toEqual({ sha256: redactionPlan.sha256, criteria: redactionPlan.criteria, selected: [first!.id, second!.id], areas: [{ page: 2, rect: [0, 0, 0.5, 0.5] }], sanitize: false })
  })

  it('prüft vor dem Senden', () => {
    const base: RedactionData = { ...INITIAL_REDACTION, catalogue: redactionCatalogue }
    expect(redactionValidation(base)).toBe('needFile')
    const file = syntheticPdf()
    expect(redactionValidation({ ...base, file })).toBe('needCriteria')
    expect(redactionValidation({ ...base, file, terms: 'x\n'.repeat(1) + Array.from({ length: 200 }, (_, n) => `t${n}`).join('\n') })).toBe('tooManyTerms')
    expect(redactionValidation({ ...base, file, terms: 'x'.repeat(201) })).toBe('termTooLong')
    expect(redactionValidation({ ...base, file: syntheticPdf('gross.pdf', 21 * 1024 * 1024) })).toBe('tooLarge')
    expect(redactionValidation({ ...base, file, patterns: ['email'] })).toBeNull()
    expect(redactionValidationText('tooLarge', redactionCatalogue, t, 'de')).toBe('Die Datei ist größer als 20 MiB.')
    expect(redactionValidationText('tooManyTerms', redactionCatalogue, t, 'de')).toBe('Höchstens 200 Begriffe sind zulässig.')
    expect(redactionValidationText('termTooLong', null, t, 'de')).toBe('Ein Begriff darf höchstens 0 Zeichen lang sein.')
    expect(redactionValidationText('needFile', null, t, 'de')).toBe('Bitte eine PDF-Datei wählen.')
    expect(redactionValidationText('needCriteria', null, t, 'de')).toBe('Bitte mindestens ein Muster oder einen Begriff angeben.')
    expect(redactionValidationText(null, null, t, 'de')).toBe('')
  })

  it('beschriftet Muster und Größen', () => {
    const ai = redactionCatalogue.patterns.find((pattern) => pattern.ai)!
    expect(redactionPatternText(ai, t)).toBe('Personennamen (KI-Erkennung)')
    expect(redactionPatternText({ ...ai, label: 'Namen' }, t)).toBe('Namen (KI)')
    expect(redactionPatternText(redactionCatalogueWithoutNer.patterns.find((pattern) => pattern.ai)!, t)).toBe('Personennamen (KI-Erkennung) (nicht eingerichtet)')
    expect(redactionPatternText(redactionCatalogue.patterns[0]!, t)).toBe('IBAN')
    expect(redactionSizeText(1500, 'de')).toBe('2 KiB')
  })
})

describe('Schwärzen: Zustandsautomat', () => {
  it('lädt den Katalog, holt den Plan mit bereinigten Begriffen und das erste Seitenbild', async () => {
    const { controller, port, planned } = await setup()
    const state = controller.store.get()
    expect(port.calls.slice(0, 2)).toEqual([
      ['plan', 'vermerk.pdf', JSON.stringify({ patterns: ['email'], terms: ['Prüfvermerk'], case_sensitive: false, whole_word: true })],
      ['preview', 'vermerk.pdf', 1],
    ])
    expect(redactionStep(state)).toBe('review')
    expect(state.selected.size).toBe(redactionPlan.candidates.length)
    expect(state.preview).toBe('blob:fa-test/image/png/7')
    expect(planned).toHaveBeenCalledWith(redactionPlan)
  })

  it('verweigert das Senden ohne Kriterien und meldet Fehler', async () => {
    const failed = vi.fn()
    const controller = createRedactionController({ port: () => fakeRedactionPort({ failing: 'plan' }), urls: fakeUrls(), callbacks: () => ({ failed }) })
    await controller.load()
    controller.selectFile(syntheticPdf())
    await controller.plan()
    expect(controller.store.get().validation).toBe('needCriteria')
    controller.setPattern('iban', true)
    controller.setPattern('iban', true)
    expect(controller.store.get().patterns).toEqual(['iban'])
    await controller.plan()
    expect(controller.store.get().error).toBe('Dienst nicht erreichbar')
    expect(failed).toHaveBeenCalledWith('Dienst nicht erreichbar')
    controller.setPattern('iban', false)
    expect(controller.store.get().patterns).toEqual([])
  })

  it('verwirft beim Laden Muster, die der Dienst nicht anbietet', async () => {
    const port = fakeRedactionPort({ catalogue: redactionCatalogueWithoutNer })
    const controller = createRedactionController({ port: () => port, urls: fakeUrls() })
    controller.setPattern('ki_namen', true)
    controller.setPattern('email', true)
    await controller.load()
    expect(controller.store.get().patterns).toEqual(['email'])
    await createRedactionController({ port: () => null }).load()
  })

  it('schaltet Fundstellen, Quellen, Gruppen und Filter', async () => {
    const { controller } = await setup()
    const [first] = redactionPlan.candidates
    controller.toggle(first!.id)
    expect(controller.store.get().selected.has(first!.id)).toBe(false)
    controller.setAll(false)
    expect(controller.store.get().selected.size).toBe(0)
    controller.setSource('email', true)
    expect(controller.store.get().selected.size).toBe(3)
    const group = redactionGroups(redactionPlan.candidates)[1]!
    controller.setGroup(group.key, true)
    controller.setGroup('gibt-es-nicht', true)
    expect(controller.store.get().selected.size).toBe(5)
    controller.setSource('email', false)
    controller.setAll(true)
    expect(controller.store.get().selected.size).toBe(redactionPlan.candidates.length)
    controller.toggleExpanded(group.key)
    let review = redactionReview(controller.store.get(), t)!
    expect(review.groups[1]!.expanded).toBe(true)
    expect(review.groups[1]!.items.map((item) => [item.number, item.page, item.text, item.extra])).toEqual([[1, 1, '', ''], [2, 1, '', '']])
    controller.setFilter('  ERIKA ')
    review = redactionReview(controller.store.get(), t)!
    expect(review.groups.map((entry) => entry.text)).toEqual(['Erika Beispiel'])
    controller.setFilter('nichts')
    expect(redactionReview(controller.store.get(), t)!.noMatch).toBe('Keine Fundstelle passt zu „nichts“.')
    controller.toggleExpanded(group.key)
    expect(controller.store.get().expanded.size).toBe(0)
  })

  it('zeigt Seiten, legt Bereiche an, verschiebt, vergrößert und entfernt sie', async () => {
    const { controller, port, urls } = await setup()
    await controller.showPage(2)
    await controller.showPage(9)
    await controller.showPage(2)
    expect(controller.store.get().page).toBe(2)
    expect(port.calls.filter((call) => call[0] === 'preview')).toEqual([['preview', 'vermerk.pdf', 1], ['preview', 'vermerk.pdf', 2]])
    await controller.showPage(1)
    expect(port.calls.filter((call) => call[0] === 'preview')).toHaveLength(2)
    expect(controller.store.get().preview).toBe('blob:fa-test/image/png/7')

    controller.pointerDown([0.1, 0.1])
    controller.pointerMove([0.3, 0.2])
    expect(redactionReview(controller.store.get(), t)!.draft).toEqual({ left: '10%', top: '10%', width: '20%', height: '10%' })
    controller.pointerUp([0.3, 0.2])
    controller.pointerDown([0.5, 0.5])
    controller.pointerUp([0.501, 0.501])
    expect(controller.addDefaultArea()).toBe(true)
    const [drawn, added] = controller.store.get().areas
    expect(drawn!.rect).toEqual([0.1, 0.1, 0.3, 0.2])
    expect(added!.rect).toEqual([0.33, 0.43, 0.63, 0.51])
    controller.startResize(drawn!.id)
    controller.pointerMove([0.4, 0.25])
    controller.pointerUp([0.4, 0.25])
    controller.nudgeArea(added!.id, 'ArrowDown', 'move', true)
    expect(controller.store.get().areas.map((area) => area.rect)).toEqual([[0.1, 0.1, 0.4, 0.25], [0.33, 0.48, 0.63, 0.56]])
    controller.pointerDown([0.6, 0.6])
    controller.cancelGesture()
    expect(controller.store.get().gesture).toBeNull()
    const review = redactionReview(controller.store.get(), t)!
    expect(review.areas.map((area) => area.removeLabel)).toEqual(['Bereich 1 auf Seite 1 entfernen', 'Bereich 2 auf Seite 1 entfernen'])
    expect(review.summary).toBe('9 von 9 Fundstellen ausgewählt, 2 eigene Bereiche')
    controller.removeArea(drawn!.id)
    expect(controller.store.get().areas).toHaveLength(1)
    expect(redactionReview(controller.store.get(), t)!.summary).toBe('9 von 9 Fundstellen ausgewählt, 1 eigener Bereich')
    controller.startMove(added!.id, [0.4, 0.5])
    controller.pointerMove([0.5, 0.4])
    controller.pointerUp([0.5, 0.4])
    expect(controller.store.get().areas[0]!.rect.map((v) => Math.round(v * 100) / 100)).toEqual([0.43, 0.38, 0.73, 0.46])
    controller.startMove('gibt-es-nicht', [0.1, 0.1])
    expect(controller.store.get().gesture).toBeNull()
    controller.back()
    expect(redactionStep(controller.store.get())).toBe('form')
    expect(urls.live.size).toBe(0)
  })

  it('hält die Grenzen eigener Bereiche ein', async () => {
    const catalogue = { ...redactionCatalogue, limits: { ...redactionCatalogue.limits, max_areas: 3, max_areas_per_page: 2 } }
    const { controller } = await setup(fakeRedactionPort({ catalogue }))
    expect(controller.addDefaultArea()).toBe(true)
    expect(controller.addDefaultArea()).toBe(true)
    expect(controller.addDefaultArea()).toBe(false)
    expect(redactionReview(controller.store.get(), t)!.areaLimit).toBe('Höchstens 2 eigene Bereiche je Seite und 3 insgesamt.')
    await controller.showPage(2)
    expect(controller.addDefaultArea()).toBe(true)
    expect(controller.addDefaultArea()).toBe(false)
    controller.removeArea(controller.store.get().areas[0]!.id)
    expect(controller.store.get().areaLimitHit).toBe(false)
  })

  it('schwärzt die Auswahl, zeigt den Bericht und gibt URLs frei', async () => {
    const { controller, port, urls, completed } = await setup()
    controller.toggle(redactionPlan.candidates[0]!.id)
    controller.addDefaultArea()
    controller.setOption('sanitize', false)
    await controller.apply()
    const apply = port.calls.find((call) => call[0] === 'apply')!
    expect(apply[2]).toMatchObject({ sha256: redactionPlan.sha256, sanitize: false, areas: [{ page: 1, rect: [0.3, 0.4, 0.6, 0.48] }] })
    expect((apply[2] as { selected: string[] }).selected).toHaveLength(redactionPlan.candidates.length - 1)
    const state = controller.store.get()
    expect(redactionStep(state)).toBe('result')
    expect(state.resultUrl).toBe('blob:fa-test/application/pdf/20')
    expect(completed).toHaveBeenCalledTimes(1)
    expect(redactionReportRows(state, t, 'de').map((row) => `${row.label}: ${row.value}`)).toEqual([
      'Geschwärzte Fundstellen: 7', 'Eigene Bereiche: 1', 'Entfernte versteckte Inhalte: 2', 'Bewusst lesbar gelassen: 0', 'Betroffene Seiten: 2', 'Dokument bereinigt: ja',
    ])
    controller.editAgain()
    expect(redactionStep(controller.store.get())).toBe('review')
    expect(redactionReportRows(controller.store.get(), t, 'de')).toEqual([])
    expect(urls.live.has('blob:fa-test/application/pdf/20')).toBe(false)
    await controller.apply()
    controller.reset()
    expect(controller.store.get()).toMatchObject({ file: null, plan: null, result: null, patterns: ['email'] })
    expect(urls.live.size).toBe(0)
  })

  it('verwirft veraltete Antworten und Seitenbildfehler', async () => {
    const port = fakeRedactionPort({ failing: 'preview' })
    const { controller } = await setup(port)
    expect(controller.store.get().previewError).toBe('Dienst nicht erreichbar')
    let resolve: (blob: Blob) => void = () => undefined
    const quick = fakeRedactionPort()
    const slow = { ...quick, preview: (file: Blob, name: string, page: number) => (page === 1 ? quick.preview(file, name, page) : new Promise<Blob>((done) => (resolve = done))) }
    const second = await setup(slow)
    const pending = second.controller.showPage(2)
    second.controller.back()
    resolve(new Blob(['spät']))
    await pending
    expect(second.urls.live.size).toBe(0)
    second.controller.selectFile(syntheticPdf())
    await second.controller.apply()
    second.controller.dispose()
  })

  it('zeigt Hinweise der Prüfansicht', async () => {
    const { controller } = await setup()
    const review = redactionReview(controller.store.get(), t)!
    expect(review.pageText).toBe('Seite 1 von 3')
    expect(review.aspect).toBe('595 / 842')
    expect(review.boxes).toHaveLength(5)
    expect(review.boxes[0]!.label).toBe('Begriff „Prüfvermerk“: Prüfvermerk – wird geschwärzt')
    expect(review.noText).toContain('Seite 3 ohne Textebene')
    expect(review.outside).toBe('')
    expect(review.hiddenText).toContain('In Metadaten stehen Treffer')
    expect(review.sources.map((entry) => entry.text)).toEqual(['Begriff „Prüfvermerk“ · 2', 'E-Mail-Adresse · 3', 'IBAN · 1', 'Personennamen (KI-Erkennung) · 3'])
    expect(review.pageButtons).toEqual([1, 2])
    expect(review.showFilter).toBe(false)
    expect(review.more).toBe('')
    expect(review.sources[0]!.pressed).toBe('true')
    controller.toggle(review.boxes[0]!.id)
    expect(redactionReview(controller.store.get(), t)!.sources[0]!).toMatchObject({ state: 'some', pressed: 'mixed' })
    const email = redactionGroups(redactionPlan.candidates)[0]!
    controller.toggleExpanded(email.key)
    const items = redactionReview(controller.store.get(), t)!.groups[0]!.items
    expect(items.map((item) => [item.page, item.text])).toEqual([[1, ''], [2, ''], [null, 'Metadaten (author)']])
    expect(redactionReview(INITIAL_REDACTION, t)).toBeNull()
  })

  it('zeigt viele Gruppen seitenweise und lange Seitenlisten gekürzt', async () => {
    const many = {
      ...redactionPlan,
      page_count: 80,
      pages: [{ page: 1, width: 842, height: 595, rotation: 90, has_text: true }],
      candidates: Array.from({ length: 250 }, (_, n) => ({ ...redactionPlan.candidates[1]!, id: `c${n}`, text: `adresse${n}@beispiel.example`, page: (n % 70) + 1, outside_view: n === 0 })),
    }
    const { controller } = await setup(fakeRedactionPort({ plan: many }))
    let review = redactionReview(controller.store.get(), t)!
    // width/height beschreiben schon die gedrehte, sichtbare Seite (Querformat).
    expect(review.aspect).toBe('842 / 595')
    expect(review.groups).toHaveLength(200)
    expect(review.more).toBe('Weitere 50 anzeigen')
    expect(review.showFilter).toBe(true)
    expect(review.morePages).toBe(true)
    expect(review.pageButtons).toHaveLength(60)
    expect(review.outside).toBe('1 Fundstelle liegt außerhalb des sichtbaren Seitenbereichs. Sie wird mitgeschwärzt, ist in der Ansicht aber nicht zu sehen.')
    controller.showMore()
    review = redactionReview(controller.store.get(), t)!
    expect(review.groups).toHaveLength(250)
    await controller.showPage(5)
    expect(redactionReview(controller.store.get(), t)!.aspect).toBe('1 / 1.414')
  })
})

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

