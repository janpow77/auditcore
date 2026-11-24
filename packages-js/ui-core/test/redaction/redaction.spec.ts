import { describe, expect, it, vi } from 'vitest'
import {
  createRedactionController,
  createRedactionRestPort,
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
    expect(redactionPatternText(ai, t)).toBe('Personennamen (KI-Erkennung) (KI)')
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
    controller.toggle(review.boxes[0]!.id)
    expect(redactionReview(controller.store.get(), t)!.sources[0]!.state).toBe('some')
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
    expect(review.aspect).toBe('595 / 842')
    expect(review.groups).toHaveLength(200)
    expect(review.more).toBe('Weitere 50 anzeigen')
    expect(review.showFilter).toBe(true)
    expect(review.morePages).toBe(true)
    expect(review.pageButtons).toHaveLength(60)
    expect(review.outside).toBe('1 Fundstellen liegen außerhalb des sichtbaren Seitenbereichs. Sie werden mitgeschwärzt, sind in der Ansicht aber nicht zu sehen.')
    controller.showMore()
    review = redactionReview(controller.store.get(), t)!
    expect(review.groups).toHaveLength(250)
    await controller.showPage(5)
    expect(redactionReview(controller.store.get(), t)!.aspect).toBe('1 / 1.414')
  })
})

describe('Schwärzen: REST-Port', () => {
  function fetchStub(responses: Response[]) {
    const calls: Array<{ url: string; init: RequestInit }> = []
    const fetch = vi.fn(async (url: RequestInfo | URL, init?: RequestInit) => {
      calls.push({ url: String(url), init: init ?? {} })
      return responses.shift()!
    })
    return { fetch, calls }
  }

  it('sendet Datei und Felder als Formular und liest den Bericht aus den Köpfen', async () => {
    const pdf = new Blob(['%PDF'], { type: 'application/pdf' })
    const { fetch, calls } = fetchStub([
      Response.json(redactionCatalogue),
      Response.json(redactionPlan),
      new Response(new Blob(['png'], { type: 'image/png' })),
      new Response(pdf, {
        headers: {
          'Content-Disposition': "attachment; filename=\"vermerk_geschw_rzt.pdf\"; filename*=UTF-8''vermerk_geschw%C3%A4rzt.pdf",
          'X-Redactions': '4', 'X-Redaction-Areas': '1', 'X-Redaction-Hidden': '2', 'X-Redaction-Deselected': 'x', 'X-Redaction-Pages': '2',
          'X-Redaction-Sanitized': 'true', 'X-Redaction-Verified': 'true',
        },
      }),
      new Response(pdf),
    ])
    const port = createRedactionRestPort({ baseUrl: '/api/redaction/', fetch, headers: { 'X-Mandant': 'demo' } })
    expect(await port.catalogue()).toEqual(redactionCatalogue)
    expect(await port.plan(pdf, 'vermerk.pdf', redactionPlan.criteria)).toEqual(redactionPlan)
    expect(await (await port.preview(pdf, 'vermerk.pdf', 2)).text()).toBe('png')
    const selection = redactionSelectionPayload(redactionPlan, new Set(), [], true)
    const result = await port.apply(pdf, 'vermerk.pdf', selection)
    expect(result.filename).toBe('vermerk_geschwärzt.pdf')
    expect(result.report).toEqual({ redactions: 4, areas: 1, hidden: 2, deselected: 0, pages: 2, sanitized: true, verified: true })
    expect((await port.apply(pdf, 'vermerk.pdf', selection)).filename).toBe('geschwärzt.pdf')
    expect(calls.map((call) => [call.url, call.init.method])).toEqual([
      ['/api/redaction/catalogue', 'GET'], ['/api/redaction/plan', 'POST'], ['/api/redaction/preview', 'POST'], ['/api/redaction/apply', 'POST'], ['/api/redaction/apply', 'POST'],
    ])
    const form = calls[2]!.init.body as FormData
    expect(form.get('page')).toBe('2')
    expect(form.get('file')).toBeInstanceOf(Blob)
    expect(JSON.parse((calls[1]!.init.body as FormData).get('criteria') as string)).toEqual(redactionPlan.criteria)
    expect(calls[3]!.init.headers).toMatchObject({ Accept: 'application/pdf', 'X-Mandant': 'demo' })
  })

  it('wirft RestError mit Code und Meldung des Dienstes', async () => {
    const { fetch } = fetchStub([
      Response.json({ error: { code: 'stale_plan', message: 'Die Datei hat sich geändert.' } }, { status: 409 }),
      new Response('kaputt', { status: 502 }),
      new Response('kaputt', { status: 500 }),
    ])
    const port = createRedactionRestPort({ baseUrl: '/api', fetch })
    const pdf = new Blob(['%PDF'])
    await expect(port.apply(pdf, 'a.pdf', redactionSelectionPayload(redactionPlan, new Set(), [], true))).rejects.toMatchObject({ status: 409, code: 'stale_plan', message: 'Die Datei hat sich geändert.' })
    await expect(port.plan(pdf, 'a.pdf', redactionPlan.criteria)).rejects.toMatchObject({ status: 502, code: 'http_error' })
    await expect(port.catalogue()).rejects.toMatchObject({ status: 500 })
  })
})
