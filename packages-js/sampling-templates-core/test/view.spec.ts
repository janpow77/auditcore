import { describe, expect, it } from 'vitest'
import { createTranslate, samplingTemplatesMessages, withMessages } from '../src/i18n/messages'
import { defaultInputs } from '../src/model/definition'
import { createContext } from '../src/model/sheet'
import { sheet } from '../src/sheets/03_MUS_1Z/index'
import { buildSections } from '../src/view/sheetView'
import { buildSummary } from '../src/view/summaryView'

const context = createContext()
const t = createTranslate()
const nbsp = (text: string): string => text.replaceAll(String.fromCharCode(160), ' ')

function rows(inputs: Record<string, string | number | null>) {
  return buildSections(sheet, inputs, sheet.compute(inputs, context), context, t).flatMap((section) => [...section.rows])
}

describe('Anzeigemodell des Rechenblatts', () => {
  it('Abschnitte in der Reihenfolge der Vorlage', () => {
    const sections = buildSections(sheet, sheet.sample.inputs, sheet.compute(sheet.sample.inputs, context), context, t)
    expect(sections.map((section) => section.id)).toEqual(['H', 'I', 'J', 'K', 'L', 'M'])
    expect(sections[0]?.reference).toBe('Art. 3')
  })

  it('Eingaben, Auswahlfelder, Ergebnisse und Prüfhinweise', () => {
    const all = rows(sheet.sample.inputs)
    const byCell = (cell: string) => all.find((row) => row.cell === cell)!
    expect(byCell('C7')).toMatchObject({ control: 'number', inputText: '48.500.000,00', link: { sheet: '02_Grundgesamtheit', overridden: true } })
    expect(byCell('C14')).toMatchObject({ control: 'number', type: 'percent', inputText: '2' })
    expect(byCell('C10')).toMatchObject({ control: 'select', value: 0.7 })
    expect(byCell('C10').options).toHaveLength(5)
    expect(byCell('C27')).toMatchObject({ control: 'output', display: '92', key: true })
    expect(nbsp(byCell('C34').display)).toBe('480.681,82 €')
    expect(byCell('C13')).toMatchObject({ control: 'check', tone: 'success', display: '✔ mittel: Wert zwischen den Eckwerten' })
    expect(byCell('C25')).toMatchObject({ control: 'check', tone: 'neutral' })
    expect(byCell('C21').formula).toBe('n = (z · BV · σ_r / (TE − AE))²')
  })

  it('„Angabe fehlt“, wo die Vorlage mit 0 weiterrechnen würde', () => {
    const inputs = { ...sheet.sample.inputs, C20: null }
    const all = rows(inputs)
    expect(all.find((row) => row.cell === 'C21')).toMatchObject({ missing: true, display: 'Angabe fehlt', missingNote: 'Es fehlt: Voraussichtliche Standardabweichung der Fehlerquoten (σ_r) (C20)' })
    // Buchwert leer, begrenzter Umfang zulässig: Die Vorlage zeigt Werte auf der Grundlage von 0 €.
    const limited = rows({ ...sheet.sample.inputs, C7: null, C24: 'Ja' })
    expect(limited.find((row) => row.cell === 'C42')).toMatchObject({ missing: true, missingNote: 'Es fehlt: Buchwert der angepassten zu prüfenden Grundgesamtheit (positive Einheiten) (BV) (C7)' })
    // Ohne begrenzten Umfang zeigt auch die Vorlage nichts: keine „Angabe fehlt“-Meldung.
    expect(rows({ ...sheet.sample.inputs, C7: null }).find((row) => row.cell === 'C42')).toMatchObject({ missing: false, missingNote: '', display: '—' })
    expect(all.find((row) => row.cell === 'C27')).toMatchObject({ missing: true, display: 'Angabe fehlt' })
    expect(all.find((row) => row.cell === 'C12')).toMatchObject({ missing: false, display: '1,036' })
    const empty = rows(defaultInputs(sheet.definition))
    expect(empty.find((row) => row.cell === 'C12')).toMatchObject({ missing: false, display: '—' })
    expect(empty.find((row) => row.cell === 'C13')).toMatchObject({ display: 'noch keine Angaben' })
    expect(empty.find((row) => row.cell === 'C7')).toMatchObject({ link: { overridden: false }, inputText: '' })
  })
})

describe('Mitlaufende Ergebnisspalte', () => {
  it('Beispielwerte: Größen wie im Gestaltungsprototyp', () => {
    const summary = buildSummary(sheet, sheet.sample.inputs, sheet.compute(sheet.sample.inputs, context), context, t)
    expect(summary).toMatchObject({ primaryValue: '92', primaryUnit: 'Einheiten', primaryNote: '' })
    expect(summary.rows.map((row) => [row.label, nbsp(row.value)])).toEqual([
      ['davon hochwertig', '4'],
      ['Zufallsschicht n_s', '88'],
      ['Auswahlintervall', '480.681,82 €'],
      ['Extrapolierter Fehler', '316.422,73 €'],
      ['Genauigkeit SE', '210.218,68 €'],
      ['Gesamtfehlerquote', '0,652 %'],
      ['Obere Fehlergrenze', '1,086 %'],
    ])
    expect(summary.hints.map((hint) => hint.text)).toEqual([
      '✔ mittel: Wert zwischen den Eckwerten',
      '✔ ≤ 2 %',
      '✔ TE > AE',
      'Nicht angewandt – Anh. I und II gelten',
      '✔ ≥ 3 Einheiten',
      '✔ keine weitere Iteration',
      '✔ GFQ und obere Fehlergrenze unter der Schwelle',
    ])
    expect(summary.gauge).toMatchObject({ threshold: 0.5 })
    expect(nbsp(summary.gauge?.description ?? '')).toBe('Gesamtfehlerquote 0,65 %, obere Fehlergrenze 1,09 %, Signifikanzschwelle 2,00 %')
  })

  it('TE ≤ AE: Umfang nicht bestimmbar, mit Grund', () => {
    const inputs = { ...sheet.sample.inputs, C17: 0.025 }
    const summary = buildSummary(sheet, inputs, sheet.compute(inputs, context), context, t)
    expect(summary).toMatchObject({ primaryValue: '', primaryNote: 'nicht bestimmbar (TE ≤ AE)', gauge: null })
    expect(summary.hints.map((hint) => hint.tone)).toContain('danger')
  })

  it('Hinweise der Webfassung sind als solche gekennzeichnet', () => {
    const inputs = { ...sheet.sample.inputs, C8: 50 }
    const summary = buildSummary(sheet, inputs, sheet.compute(inputs, context), context, t)
    expect(summary.hints.filter((hint) => hint.source === 'web')).toEqual([expect.objectContaining({ id: 'size-exceeds-population', tone: 'warning' })])
  })
})

describe('Als 0 gerechnete fehlende Angaben', () => {
  it('Blatt 03: ohne s_r rechnet die Webfassung wie die Vorlage mit 0 und weist es aus', () => {
    const inputs = { ...sheet.sample.inputs, C39: null }
    const results = sheet.compute(inputs, context)
    expect(results.C43).toBe(0)
    expect(results.C52).toBe('✔ GFQ und obere Fehlergrenze unter der Schwelle')
    expect(sheet.zeroAssumed?.(results)).toEqual([{ input: 'C39', cells: ['C43', 'C46', 'C47', 'C48', 'C51', 'C52'] }])
    const all = rows(inputs)
    const note = 'Keine Angabe, daher mit 0 berechnet: Standardabweichung der Fehlerquoten in der Stichprobe der Zufallsschicht (s_r) (C39)'
    expect(all.filter((row) => row.zeroNote).map((row) => row.cell)).toEqual(['C43', 'C46', 'C47', 'C48', 'C51', 'C52'])
    // Die Würdigung ist bestanden, steht aber nicht uneingeschränkt grün da: Ein Hinweis in Warnfarbe schränkt das Ergebnis ein.
    expect(all.find((row) => row.cell === 'C52')).toMatchObject({ zeroNote: note, tone: 'warning' })
    const hints = buildSummary(sheet, inputs, results, context, t).hints
    expect(hints.find((hint) => hint.id === 'zero-C39')).toEqual({ id: 'zero-C39', tone: 'warning', source: 'web', text: note })
    expect(hints.findIndex((hint) => hint.id === 'zero-C39')).toBe(hints.findIndex((hint) => hint.id === 'C52') + 1)
  })

  it('kein Hinweis, solange die Genauigkeit gar nicht berechnet ist oder s_r angegeben wurde', () => {
    expect(sheet.zeroAssumed?.(sheet.compute(sheet.sample.inputs, context))).toEqual([])
    expect(sheet.zeroAssumed?.(sheet.compute({ ...sheet.sample.inputs, C39: 0 }, context))).toEqual([])
    expect(sheet.zeroAssumed?.(sheet.compute({ ...sheet.sample.inputs, C39: null, C10: null }, context))).toEqual([])
  })

  it('englisch: „Not provided, therefore calculated with 0.“', () => {
    const en = createTranslate(samplingTemplatesMessages, 'en')
    expect(en('zeroAssumed')).toBe('Not provided, therefore calculated with 0.')
    expect(t('zeroAssumed')).toBe('Keine Angabe, daher mit 0 berechnet.')
  })
})

describe('Texte', () => {
  it('Anwendungen können Texte überschreiben und Englisch liefern', () => {
    const catalogs = withMessages({ de: { exportResult: 'Export' }, en: { exportResult: 'Export result' } })
    expect(createTranslate(catalogs)('exportResult')).toBe('Export')
    expect(createTranslate(catalogs, 'en')('exportResult')).toBe('Export result')
    expect(createTranslate(catalogs, 'en')('menuSaveHint')).toBe(samplingTemplatesMessages.de.menuSaveHint)
    expect(createTranslate(catalogs, 'en')('menuSave')).toBe('Save working file')
    expect(t('sheetNumber', { number: '03' })).toBe('Blatt 03')
  })
})
