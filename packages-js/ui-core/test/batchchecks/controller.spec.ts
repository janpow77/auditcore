import { describe, expect, it } from 'vitest'
import {
  batchchecksAffectedText,
  batchchecksAutoMapping,
  batchchecksCellValue,
  batchchecksFindingRows,
  batchchecksJsonDocuments,
  batchchecksMessages,
  batchchecksMetricRows,
  batchchecksRuleRows,
  buildBatchchecksRequest,
  createBatchchecksController,
  createBatchchecksMemoryPort,
  translator,
  type BatchchecksPort,
} from '../../src'
import { batchAnswer, batchCatalogue, batchCsv, fakeBatchchecksPort, textFile } from './fake-port'

const t = translator(batchchecksMessages, 'de')
const field = (name: string) => batchCatalogue.fields.find((entry) => entry.name === name)!

function controller(port: BatchchecksPort | null = fakeBatchchecksPort()) {
  const events: string[] = []
  const created = createBatchchecksController({
    port: () => port,
    callbacks: () => ({ completed: (answer) => events.push(`ok:${answer.summary.findings}`), failed: (message) => events.push(message) }),
  })
  return { created, events }
}

describe('Eingabe der Bestandsprüfung', () => {
  it('ordnet Spalten über die Spaltennamen des Katalogs zu', () => {
    const mapping = batchchecksAutoMapping(batchCatalogue.fields, ['Beleg', 'Re.-Nr.', 'Brutto', 'Unbekannt', 'total'])
    expect(mapping).toMatchObject({ ref: 0, invoice_number: 1, gross_amount: 2, net_amount: null })
  })

  it('liest Zahlenfelder deutsch, Prozent der OCR-Konfidenz als Anteil, Unlesbares unverändert', () => {
    expect(batchchecksCellValue('1.234,56', field('gross_amount'), ',')).toBe(1234.56)
    expect(batchchecksCellValue('93 %', field('ocr_confidence'), ',')).toBeCloseTo(0.93)
    expect(batchchecksCellValue('19%', field('vat_rate'), ',')).toBe(19)
    expect(batchchecksCellValue('NaN', field('net_amount'), ',')).toBe('NaN')
    expect(batchchecksCellValue('  ', field('description'), ',')).toBeNull()
  })

  it('erkennt JSON-Listen, {"documents": …} und einzelne Läufe der Belegerkennung', () => {
    expect(batchchecksJsonDocuments('[{"invoice_number": "1"}]')).toHaveLength(1)
    expect(batchchecksJsonDocuments('{"documents": [{}, {}]}')).toHaveLength(2)
    expect(batchchecksJsonDocuments('{"contract": "documents_extraction/1", "fields": []}')).toHaveLength(1)
    expect(batchchecksJsonDocuments('{"x": 1}')).toBeNull()
    expect(batchchecksJsonDocuments('[1, 2]')).toBeNull()
    expect(batchchecksJsonDocuments('kein json')).toBeNull()
  })

  it('prüft vor dem Senden: Daten, Zuordnung, Grenze, Gesamtvolumen', () => {
    const base = { catalogue: batchCatalogue, table: null, json: null, mapping: {}, decimal: ',' as const, totalVolume: '', supplementary: true }
    expect(buildBatchchecksRequest(base)).toEqual({ ok: false, error: 'noData' })
    expect(buildBatchchecksRequest({ ...base, json: [] })).toEqual({ ok: false, error: 'noRows' })
    const tooMany = { ...batchCatalogue, limits: { ...batchCatalogue.limits, max_documents: 1 } }
    expect(buildBatchchecksRequest({ ...base, catalogue: tooMany, json: [{}, {}] })).toEqual({ ok: false, error: 'tooMany' })
    const table = { delimiter: ';' as const, header: ['Beleg'], rows: [['1']] }
    expect(buildBatchchecksRequest({ ...base, table, mapping: { ref: 0 } })).toEqual({ ok: false, error: 'noColumns' })
    expect(buildBatchchecksRequest({ ...base, json: [{}], totalVolume: 'viel' })).toEqual({ ok: false, error: 'totalVolume' })
    expect(buildBatchchecksRequest({ ...base, json: [{}], totalVolume: '48.500,00' })).toEqual({
      ok: true, request: { documents: [{}], options: { supplementary: true, total_volume: 48500 } },
    })
  })
})

describe('createBatchchecksController', () => {
  it('liest die CSV ein, ordnet zu, prüft und exportiert über den Port', async () => {
    const port = fakeBatchchecksPort()
    const { created, events } = controller(port)
    await created.load()
    await created.readFile(textFile(batchCsv, 'bestand.csv'))
    expect(created.store.get().mapping).toMatchObject({ ref: 0, invoice_number: 1, gross_amount: 10, ocr_confidence: 11 })
    created.setTotalVolume('48.500,00')
    await created.check()
    const [, request] = port.calls[1]!
    expect(request?.documents).toHaveLength(10)
    expect(request?.documents[0]).toMatchObject({ ref: 'B-001', gross_amount: 11900, ocr_confidence: 0.97 })
    expect(request?.options).toEqual({ supplementary: true, total_volume: 48500 })
    expect(events).toEqual([`ok:${batchAnswer.summary.findings}`])
    const file = await created.exportRun('csv')
    expect(file?.filename).toBe('befunde-bestand.csv')
    expect(port.calls[2]?.[2]).toBe('csv')
  })

  it('nimmt JSON-Dateien als Belegliste und meldet unbrauchbare Dateien', async () => {
    const { created } = controller()
    await created.load()
    await created.readFile(textFile('{"documents": [{"invoice_number": "A-1"}]}', 'bestand.json'))
    expect(created.store.get().json).toHaveLength(1)
    await created.readFile(textFile('{"x": 1}', 'kaputt.json'))
    expect(created.store.get().validation).toBe('json')
    await created.check()
    expect(created.store.get().validation).toBe('noData')
  })

  it('Kopfzeile umschalten ordnet neu zu; Fehler des Ports werden gemeldet', async () => {
    const { created, events } = controller(fakeBatchchecksPort({ failing: 'run' }))
    await created.load()
    created.loadText('bestand.csv', batchCsv)
    created.setHasHeader(false)
    expect(created.store.get().mapping.invoice_number).toBeNull()
    created.setHasHeader(true)
    created.setColumn('description', null)
    await created.check()
    expect(created.store.get().error).toBe('Dienst nicht erreichbar')
    expect(events).toEqual(['Dienst nicht erreichbar'])
  })

  it('ohne Port: nichts geladen, kein Export', async () => {
    const { created } = controller(null)
    await created.load()
    expect(created.store.get().catalogue).toBeNull()
    expect(await created.exportRun('json')).toBeNull()
  })
})

describe('Anzeige', () => {
  it('Regeln, Befunde mit betroffenen Belegen und Kennzahlen', () => {
    const rules = batchchecksRuleRows(batchAnswer, t)
    expect(rules.map((row) => row.code)).toContain('ERG-02')
    expect(rules.find((row) => row.code === 'C-09')?.status).toBe('1 Befund(e), 2 Beleg(e)')
    expect(rules.find((row) => row.code === 'C-10')?.status).toBe('Ergebnis des Laufs')
    const duplicates = batchchecksFindingRows(batchAnswer, 'C-09', t)
    expect(duplicates).toHaveLength(1)
    expect(duplicates[0]?.affected).toBe('B-003, B-004')
    const sum = batchAnswer.findings.find((finding) => finding.rule === 'C-08')!
    expect(batchchecksAffectedText(sum, batchAnswer, t)).toBe('Gesamtbestand')
    const many = { ...sum, documents: Array.from({ length: 12 }, (_, index) => index % 10) }
    expect(batchchecksAffectedText(many, batchAnswer, t)).toMatch(/… und 2 weitere$/)
    expect(batchchecksMetricRows(batchAnswer, t, 'de')[1]?.value).toMatch(/^50,0\s%$/)
  })

  it('Speicherport liefert Katalog und Antwort', async () => {
    const port = createBatchchecksMemoryPort(batchCatalogue, batchAnswer)
    expect((await port.catalogue()).contract).toBe('documents_batch_checks/1')
    expect((await port.exportRun({ documents: [] }, 'json')).filename).toBe('befunde-bestand.json')
  })
})
