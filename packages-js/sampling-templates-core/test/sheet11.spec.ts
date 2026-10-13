import { describe, expect, it } from 'vitest'
import { createTranslate } from '../src/i18n/messages'
import { cellsOf, defaultInputs, fieldsOf, findField, inputFields, named } from '../src/model/definition'
import { evaluateSheet } from '../src/model/evaluate'
import { TEMPLATE_POLICY } from '../src/model/policy'
import { subsampleTargets } from '../src/model/list'
import { SUMMARY_CELLS, createContext, summaryOf } from '../src/model/sheet'
import { STRATA_COLUMNS } from '../src/model/strata'
import type { CellValue, WebHint } from '../src/model/types'
import { en as shared } from '../src/sheets/01_Parameter/texts.en'
import { sheet } from '../src/sheets/11_SRS_2Z_S/index'
import { en } from '../src/sheets/11_SRS_2Z_S/texts.en'
import { INCREASE_INTERPRETATION } from '../src/sheets/shared/srs'
import { strataRows } from '../src/view/sheetView'
import { buildSummary } from '../src/view/summaryView'
import { caseInputs, loadGolden } from './golden'

type Inputs = Record<string, CellValue>

const context = createContext()
const t = createTranslate()
const sample: Inputs = sheet.sample.inputs
const run = (changes: Inputs = {}): Record<string, CellValue> => ({ ...sheet.compute({ ...sample, ...changes }, context) })
/** Variante „wie die Vorlage“: Werte ohne Grundlage stehen wie in der Vorlage. */
const likeTemplate = createContext({ policy: TEMPLATE_POLICY })
const template = (changes: Inputs = {}): Record<string, CellValue> => ({ ...sheet.compute({ ...sample, ...changes }, likeTemplate) })
const STANDARD = 'Standard (Art. 5 Abs. 6 Buchst. a)'
const GLOBAL = 'Global (Art. 5 Abs. 6 Buchst. b)'
const INCREASE = 'Erhöhung bei begrenztem Umfang (Art. 5 Abs. 7 UAbs. 4 Buchst. a)'
const NONE = 'keine Neuberechnung'
const NOT_APPLICABLE = '✖ nicht anwendbar (Nenner ≤ 0)'
/** Zeilen mit Eingaben je Schicht. */
const INPUT_ROWS = ['11', '12', '13', '14', '29', '30', '49', '50', '51', '52', '57', '58', '59', '84', '85', '86', '87']
/** Berechnete Schichtzeilen. */
const FORMULA_ROWS = ['31', '44', '45', '46', '65', '66', '67', '70', '76', '77', '78', '79', '89', '90']
/** Hohe Standardabweichung der Stichprobe in Zeitraum 1: Der Nenner des Standardansatzes wird negativ. */
const NEGATIVE: Inputs = { D51: 30000, E51: 30000, F51: 30000 }
const PRECISION_CELLS = ['C93', 'C96', 'C97', 'C98', 'C101', 'C102']
const nulls = (count: number): null[] => Array.from({ length: count }, () => null)

/** Dieselben Werte einer Schicht in eine andere Spalte verschoben. */
function moved(inputs: Inputs, from: string, to: string): Inputs {
  const result: Inputs = { ...inputs }
  for (const row of INPUT_ROWS) {
    result[`${to}${row}`] = inputs[`${from}${row}`] ?? null
    result[`${from}${row}`] = null
  }
  return result
}

describe('Blatt 11_SRS_2Z_S: Aufbau', () => {
  it('Beispielwerte mit drei Schichten ergeben ein vollständiges Ergebnis', () => {
    const results = run()
    const result = named(sheet.definition, results)
    expect(results).toMatchObject({ C11: 250, C13: 235, C15: 51500000, C16: 485, C34: 50, C42: 50, C44: 28, C45: 26, C57: 240, C61: 54900000, C69: 18, C72: 43, C74: 43, C76: 0, C77: 19, C78: 28, C80: 54 })
    expect([results.D44, results.E44, results.F44, results.G44]).toEqual([13, 10, 5, null])
    expect([results.D77, results.E77, results.F77, results.G77]).toEqual([9, 6, 4, null])
    expect(result.weightedDeviation).toBeCloseTo(9371.2106, 3)
    expect(result.projectedError).toBeCloseTo(254992.71, 2)
    expect(result.precision).toBeCloseTo(182536.86, 2)
    expect(result.totalErrorRate).toBeCloseTo(0.0046446759, 9)
    expect(result.checkMinimumSize).toBe('✔ ≥ 30 Einheiten')
    expect(result.assessment).toBe('✔ GFQ und obere Fehlergrenze unter der Schwelle')
    expect(result.stratumUnitsPeriod1).toBe(250)
    expect(result.stratumSampleSizePeriod2).toBe(19)
  })

  it('jede Zelle und jeder Alias kommt genau einmal vor; Schichtzeilen lösen sich in 20 Zellen auf', () => {
    const fields = fieldsOf(sheet.definition)
    expect(new Set(fields.map((field) => field.cell)).size).toBe(fields.length)
    expect(new Set(fields.map((field) => field.alias)).size).toBe(fields.length)
    for (const field of fields) expect(field.alias).toMatch(/^[a-z][A-Za-z0-9]*$/)
    expect(cellsOf(findField(sheet.definition, 'D11')!)).toHaveLength(20)
    expect(findField(sheet.definition, 'C57')?.alias).toBe('stratumUnitsPeriod2')
    expect(findField(sheet.definition, 'AM87')?.alias).toBe('stratumSampleRatioDeviationPeriod2')
    expect(strataRows(sheet)).toEqual(INPUT_ROWS)
    expect(fields.filter((field) => field.columns && field.kind !== 'input').map((field) => field.cell.slice(1))).toEqual(FORMULA_ROWS)
    // Tabellenköpfe („Zufallsschicht“) sind keine Felder.
    for (const row of [10, 28, 43, 48, 56, 64, 75, 83, 88]) expect(findField(sheet.definition, `D${row}`)).toBeUndefined()
  })

  it('der Rechenkern füllt jede Zelle der Definition, die Summenzellen und die Ergebnisübersicht', () => {
    for (const inputs of [sample, {}]) {
      const cells = Object.keys(sheet.compute(inputs, context))
      for (const field of fieldsOf(sheet.definition)) {
        for (const cell of cellsOf(field)) expect(cells).toContain(cell)
        if (field.total) expect(cells).toContain(field.total)
      }
      for (const cell of Object.values(SUMMARY_CELLS)) expect(cells).toContain(cell)
    }
  })

  it('Vorgaben der Vorlage, keine Verknüpfung zu Blatt 02, keine Übernahme aus Blatt 17', () => {
    expect(defaultInputs(sheet.definition)).toEqual({ C19: 'zweiseitig', C22: 0.02, C33: STANDARD, C36: 'Nein', C37: 'Nein' })
    const cells = inputFields(sheet.definition).flatMap(cellsOf)
    for (const cell of Object.keys(sample)) expect(cells).toContain(cell)
    expect(fieldsOf(sheet.definition).filter((field) => field.kind === 'link' || field.link)).toEqual([])
    expect(subsampleTargets(sheet.definition)).toEqual([])
    const linked = createContext({ sheets: { '02_Grundgesamtheit': { C51: 1000, C52: 40 } } })
    expect(sheet.compute(sample, linked)).toEqual(sheet.compute(sample, context))
  })

  it('die Ergebnisübersicht N3–N11 liest C61, C92, C91, C93, C94, C95, C80 und C100', () => {
    const results = run({ C94: 1200, C95: 300 })
    expect(results.N3).toBe('Einfaches Zufallsstichprobenverfahren, 2 Zeiträume, geschichtet')
    expect([results.N4, results.N5, results.N6, results.N7, results.N8, results.N9, results.N10, results.N11]).toEqual([results.C61, results.C92, results.C91, results.C93, 1200, 300, results.C80, results.C100])
    expect(summaryOf(sheet.id, results)).toMatchObject({ sheet: '11_SRS_2Z_S', bookValue: 54900000, exhaustiveError: 25600, sampleSize: 54, systemicErrors: 1200, anomalousErrors: 300 })
    // Leeres Formular: nur die freiwilligen Einzelbeträge zählen 0; Buchwert und Stichprobenumfang bleiben offen (die Vorlage zeigt 0).
    expect(sheet.compute({}, context)).toMatchObject({ N4: null, N5: null, N6: 0, N7: null, N8: 0, N9: 0, N10: null, N11: null })
    expect(sheet.compute({}, likeTemplate)).toMatchObject({ N4: 0, N10: 0 })
  })

  it('die Erhöhung bei begrenztem Umfang ist als Auslegung der Vorlage gekennzeichnet', () => {
    expect(fieldsOf(sheet.definition).filter((field) => field.interpretation).map((field) => [field.cell, field.interpretation])).toEqual([['D77', INCREASE_INTERPRETATION]])
  })
})

describe('Blatt 11_SRS_2Z_S: Schichten', () => {
  it('dieselben Werte in Spalte D und in Spalte AA ergeben dieselben Ergebnisse', () => {
    for (const approach of [STANDARD, GLOBAL, INCREASE, NONE]) {
      const inputs = { ...sample, C33: approach }
      const base = sheet.compute(inputs, context)
      const shifted = sheet.compute(moved(inputs, 'D', 'AA'), context)
      for (const row of FORMULA_ROWS) {
        expect(shifted[`AA${row}`], `${approach} Zeile ${row}`).toEqual(base[`D${row}`])
        expect(shifted[`E${row}`], `${approach} Zeile ${row}`).toEqual(base[`E${row}`])
      }
      for (const field of fieldsOf(sheet.definition)) {
        const cell = field.columns ? field.total : field.cell
        if (cell) expect(shifted[cell], `${approach} ${cell}`).toEqual(base[cell])
      }
      for (const cell of Object.values(SUMMARY_CELLS)) expect(shifted[cell], cell).toEqual(base[cell])
      expect([shifted.D44, shifted.D77, shifted.D90]).toEqual([null, null, 0])
    }
  })

  it('die achte Schicht rechnet mit und ist als Hinweis der Webfassung gekennzeichnet', () => {
    const eight: Inputs = { ...sample }
    for (const column of ['G', 'H', 'I', 'J', 'AA']) for (const row of INPUT_ROWS) eight[`${column}${row}`] = sample[`F${row}`] ?? null
    const results = sheet.compute(eight, context)
    expect(results.C11).toBe(250 + 5 * 40)
    expect(results.C57).toBe(240 + 5 * 47)
    expect(results.AA44).toBe(results.F44)
    expect(results.AA77).toBe(results.F77)
    expect(results.AA90).toBe(results.F90)
    for (const row of ['44', '45', '77', '78']) expect(results[`C${row}`], row).toBe(STRATA_COLUMNS.reduce((total, column) => total + ((results[`${column}${row}`] as number | null) ?? 0), 0))
    expect(sheet.webHints?.(eight, results, context).map((hint) => hint.id)).toContain('strata-beyond-template')
    expect(sheet.webHints?.(sample, run(), context).map((hint) => hint.id)).toEqual(['strata-sum-exceeds-size'])
    // Die achte Schicht zählt auch, wenn sie nur in Zeitraum 2 belegt ist.
    expect(sheet.webHints?.({ ...sample, AA57: 20 }, run({ AA57: 20 }), context).map((hint) => hint.id)).toContain('strata-beyond-template')
  })

  it('eine Schicht nur in Zeitraum 1 bzw. nur in Zeitraum 2', () => {
    const first = run({ G11: 36, G12: 3300000, G13: 34, G14: 3100000, G29: 12000, G30: 11500, G49: 370000, G50: 1900, G52: 3000 })
    expect([first.G44, first.G45, first.G78]).toEqual([expect.any(Number), expect.any(Number), first.G44])
    expect([first.G67, first.G77, first.G79]).toEqual([0, null, null])
    const second = run({ G57: 35, G58: 3200000, G59: 11800, G84: 280000, G85: 1400, G87: 2900 })
    expect([second.G44, second.G45, second.G46, second.G65, second.G66, second.G78]).toEqual([null, null, null, null, 0, null])
    expect(second.G77).toBe(3)
    expect(second.G79).toBe('✔ ≥ 3')
    expect(second.G89).toBeCloseTo(16000, 6)
    // Keine Neuberechnung: MAX(3; leere Textzelle) = 3; Erhöhung: Rechnung mit der leeren Textzelle ist ein Fehlerwert.
    expect(run({ G57: 35, G58: 3200000, G59: 11800, C33: NONE }).G77).toBe(3)
    // Der Prüfhinweis ohne Umfang ist ein Wert ohne Grundlage: Die Vorlage zeigt „✔ ≥ 3“, die Webfassung nichts.
    const increase: Inputs = { G57: 35, G58: 3200000, G59: 11800, C33: INCREASE }
    expect([run(increase).G77, run(increase).G79]).toEqual([null, null])
    expect(template(increase).G79).toBe('✔ ≥ 3')
  })

  it('weniger als drei Einheiten je Zufallsschicht: Zeile 46 meldet es, Zeile 77 hebt auf 3 an', () => {
    const small: Inputs = { G11: 5, G12: 300000, G13: 4, G14: 250000, G29: 4000, G30: 4000, G57: 6, G58: 320000, G59: 4200, C33: NONE }
    const results = run(small)
    expect([results.G44, results.G46, results.G45, results.G77, results.G79]).toEqual([1, '✖ < 3', 1, 3, '✔ ≥ 3'])
    const summary = buildSummary(sheet, { ...sample, ...small }, results, context, t)
    expect(summary.hints).toContainEqual(expect.objectContaining({ id: 'G46', text: 'Schicht 4: ✖ < 3', tone: 'danger' }))
  })

  it('ohne Umfang zeigt die Vorlage „✔ ≥ 3“ und die Summe 0 – Werte ohne Grundlage; fehlt nur eine Angabe, bleibt alles offen', () => {
    const none = run({ C25: 0.025 })
    expect([none.C34, none.C42, none.D44, none.C44, none.D46]).toEqual(['TE ≤ AE', null, null, null, null])
    const shown = template({ C25: 0.025 })
    expect([shown.C34, shown.C42, shown.D44, shown.C44, shown.D46]).toEqual(['TE ≤ AE', null, null, 0, '✔ ≥ 3'])
    const open = run({ C25: null })
    expect([open.C34, open.C42, open.D44, open.C44, open.D46, open.D79]).toEqual(nulls(6))
  })
})

describe('Blatt 11_SRS_2Z_S: Neuberechnung für Zeitraum 2', () => {
  it('die vier Ansätze: Standard, global, Erhöhung, keine Neuberechnung', () => {
    const [standard, global, increase, none] = [STANDARD, GLOBAL, INCREASE, NONE].map((approach) => run({ C33: approach, D59: 20000, E59: 24000, F59: 21000 }))
    // Standard: Aufteilung von C69 nach N_h2/N_2.
    expect(standard!.D77).toBe(Math.ceil((115 / 240) * (standard!.C69 as number)))
    expect(standard!.C78).toBe(standard!.C44)
    // Global: Aufteilung von C74 nach N_h2/N, Zusatzeinheiten für Zeitraum 1.
    expect(global!.D77).toBe(Math.ceil((115 / 490) * (global!.C74 as number)))
    expect(global!.C76).toBeGreaterThan(0)
    expect(global!.D78).toBe((global!.D44 as number) + (global!.D76 as number))
    expect(standard!.C76).toBe(global!.C76)
    // Keine Neuberechnung: geplanter Umfang; Erhöhung ohne Zuwachs gegenüber der Prognose ebenso.
    expect([none!.D77, none!.E77, none!.F77]).toEqual([none!.D45, none!.E45, none!.F45])
    expect(increase!.D77).toBe(Math.ceil(12 * (11200000 / 10800000)))
    expect(increase!.E77).toBe(increase!.E45)
    expect(run({ C33: null }).C77).toBe(none!.C77)
    expect(new Set([standard!.C80, global!.C80, increase!.C80, none!.C80]).size).toBe(4)
  })

  it('Erhöhung: der größere der Quotienten Ist/Prognose (Einheiten, Buchwert), mindestens 1', () => {
    expect(run({ C33: INCREASE, D57: 150 }).D77).toBe(Math.ceil(12 * (150 / 110)))
    expect(run({ C33: INCREASE, D57: 90, D58: 9000000 }).D77).toBe(12)
    expect(run({ C33: INCREASE, D58: null }).D77).toBe(Math.ceil(12 * (115 / 110)))
  })

  it('aktualisierte Fehlerquote: leer = Wert aus Abschnitt I', () => {
    expect(run().C63).toBeCloseTo(0.007 * 54900000, 6)
    expect(run({ C60: 0.012 }).C63).toBeCloseTo(0.012 * 54900000, 6)
    expect(run({ C60: 0 }).C63).toBe(0)
    expect(run({ C25: null, C60: 0.012 }).C63).toBeCloseTo(0.012 * 54900000, 6)
  })

  it('Standardabweichung Zeitraum 1: s aus der Stichprobe, ersatzweise σ', () => {
    expect(run().D65).toBe(7600)
    expect(run({ D51: null }).D65).toBe(8000)
    expect(run({ D51: 0 }).D65).toBe(0)
  })

  it('negativer Nenner im Standardansatz: Text in C69, kein Umfang für Zeitraum 2', () => {
    const results = run(NEGATIVE)
    expect(results.C68).toBeLessThan(0)
    expect(results.C69).toBe(NOT_APPLICABLE)
    // Die Vorlage: Summe 0 der leeren Zeile 77, Gesamtstichprobe 35, „✔ ≥ 3“ (leere Textzelle > 3), Genauigkeit 0 – alles Werte ohne Grundlage.
    const shown = template(NEGATIVE)
    expect([shown.D77, shown.C77, shown.C78, shown.C80, shown.C81]).toEqual([null, 0, 28, 35, null])
    expect([shown.D79, shown.E79, shown.F79]).toEqual(['✔ ≥ 3', '✔ ≥ 3', '✔ ≥ 3'])
    expect([shown.D90, shown.C90, shown.C93]).toEqual([null, 0, 0])
    expect(shown.C96).toBe(shown.C92)
    // Die Webfassung zeigt sie nicht.
    expect([results.D77, results.E77, results.F77, results.C77, results.C80, results.C81]).toEqual(nulls(6))
    expect(results.C78).toBe(28)
    expect([results.D79, results.E79, results.F79, results.D90, results.C90, results.C93, results.C96, results.C102]).toEqual(nulls(8))
    expect(results.C92).toBe(shown.C92)
    // Hinweis je in Zeitraum 2 belegter Schicht, mit Schichtnummer.
    const hints = sheet.webHints?.({ ...sample, ...NEGATIVE }, results, context) ?? []
    expect(hints.map((hint) => hint.id)).toEqual(['strata-sum-exceeds-size', 'negative-denominator-1', 'negative-denominator-2', 'negative-denominator-3'])
    expect(hints[2]?.text).toMatch(/^Schicht 2: Nenner der Standardneuberechnung ist nicht positiv/)
    expect(sheet.zeroAssumed?.(results)).toEqual([])
  })

  it('negativer Nenner in den anderen Ansätzen: C69 zeigt den Text, die Umfänge folgen dem gewählten Ansatz', () => {
    const expected: [string, number, number, number][] = [[GLOBAL, 126, 131, 264], [INCREASE, 28, 28, 63], [NONE, 26, 28, 61]]
    for (const [approach, second, first, total] of expected) {
      const results = run({ ...NEGATIVE, C33: approach })
      expect(results.C69, approach).toBe(NOT_APPLICABLE)
      expect([results.C77, results.C78, results.C80, results.C81], approach).toEqual([second, first, total, '✔ ≥ 30 Einheiten'])
      expect(results.C93, approach).toBeGreaterThan(0)
      expect(sheet.webHints?.(sample, results, context).filter((hint) => hint.id.startsWith('negative-denominator'))).toEqual([])
    }
  })

  it('Mindestumfang des Geschäftsjahres: 30 erreicht, 28 verfehlt', () => {
    const single: Inputs = { C7: 0, C8: 0, C53: 0, C54: 0, C55: 0, C33: NONE, C36: 'Ja', C37: 'Ja', D11: 100, D13: 100, D29: 500, D30: 500 }
    for (const column of ['E', 'F']) for (const row of INPUT_ROWS) single[`${column}${row}`] = null
    const reached = run({ ...single, C9: 0 })
    expect([reached.C42, reached.D44, reached.D77, reached.C80, reached.C81]).toEqual([30, 15, 15, 30, '✔ ≥ 30 Einheiten'])
    const missed = run({ ...single, C9: 2 })
    expect([missed.C42, missed.D44, missed.D77, missed.C80, missed.C81]).toEqual([28, 14, 14, 28, '✖ < 30 Einheiten (Art. 5 Abs. 5)'])
  })
})

describe('Blatt 11_SRS_2Z_S: fehlende Angaben', () => {
  it('fehlt eine Standardabweichung der Variablen q, ist ihr Beitrag 0 und wird ausgewiesen (je Zeitraum und Schicht)', () => {
    const full = run()
    expect(sheet.zeroAssumed?.(full)).toEqual([])
    for (const input of ['D52', 'E52', 'F52', 'D87', 'E87', 'F87']) {
      const column = input.slice(0, 1)
      const results = run({ [input]: null })
      expect(results[`${column}90`], input).toBeGreaterThan(0)
      expect(results[`${column}90`], input).toBeLessThan(full[`${column}90`] as number)
      expect(results.C93, input).toBeLessThan(full.C93 as number)
      expect(sheet.zeroAssumed?.(results), input).toEqual([{ input, cells: [`${column}90`, 'C90', ...PRECISION_CELLS] }])
    }
    const all = run({ D52: null, E52: null, F52: null, D87: null, E87: null, F87: null })
    expect([all.D90, all.C90, all.C93]).toEqual([0, 0, 0])
    expect(sheet.zeroAssumed?.(all).map((entry) => entry.input)).toEqual(['D52', 'D87', 'E52', 'E87', 'F52', 'F87'])
    const ninth = run({ AB11: 30, AB12: 2000000, AB29: 9000, AB49: 300000, AB50: 0, AB57: 28, AB58: 1900000, AB59: 9000, AB84: 280000, AB85: 0 })
    expect(sheet.zeroAssumed?.(ninth).map((entry) => entry.input)).toEqual(['AB52', 'AB87'])
    // Nicht belegte Schicht bzw. nicht belegter Zeitraum: keine Meldung zu s_qh.
    expect(sheet.zeroAssumed?.(run({ G57: 35, G58: 3200000, G59: 11800, G84: 280000, G85: 1400, G87: 2900 }))).toEqual([])
    // Offene Genauigkeit: nichts wurde mit 0 gerechnet.
    expect(sheet.zeroAssumed?.(run({ E52: null, C25: null }))).toEqual([])
  })

  it('fehlt σ Zeitraum 1 einer belegten Schicht, bleiben Gesamtumfang und Folgegrößen offen', () => {
    const results = run({ E29: null })
    expect([results.E31, results.C31, results.C32, results.C34, results.C42, results.E44, results.C44, results.C45, results.C66, results.C68, results.C69, results.C77, results.C78, results.C80, results.C93, results.C102]).toEqual(nulls(16))
    // s_eh liegt vor: Zeile 65 und der globale Ansatz sind bestimmt.
    expect([results.E65, results.C72]).toEqual([10400, 43])
    expect(results.C92).toBeCloseTo(254992.71, 2)
    const both = run({ E29: null, E51: null })
    expect([both.E65, both.E70, both.C70, both.C72, both.C74]).toEqual(nulls(5))
    // Eine nicht belegte Schicht braucht keine Standardabweichung.
    expect(run({ G29: null, G30: null, G59: null })).toEqual(run())
  })

  it('fehlt σ Zeitraum 2 (Prognose bzw. aktualisiert) einer belegten Schicht, bleibt der davon abhängige Umfang offen', () => {
    const forecast = run({ E30: null })
    expect([forecast.E31, forecast.C31, forecast.C34, forecast.C42, forecast.C69, forecast.C80]).toEqual(nulls(6))
    expect(forecast.C72).toBe(43)
    const updated = run({ E59: null })
    expect([updated.C34, updated.C42, updated.C44]).toEqual([50, 50, 28])
    expect([updated.E67, updated.C67, updated.C69, updated.E70, updated.C70, updated.C72, updated.C74, updated.E77, updated.C77, updated.C80, updated.C81, updated.C93]).toEqual(nulls(12))
    expect(updated.C78).toBe(28)
    // Keine Neuberechnung: Der Umfang für Zeitraum 2 hängt nicht an der aktualisierten Standardabweichung.
    const none = run({ E59: null, C33: NONE })
    expect([none.C77, none.C80]).toEqual([26, 61])
    expect(none.C93).toBeGreaterThan(0)
  })

  it('fehlen Wesentlichkeitsschwelle oder voraussichtliche Fehlerquote, bleiben die Umfänge offen', () => {
    const rate = run({ C25: null })
    expect([rate.C26, rate.C34, rate.C42, rate.C63, rate.C68, rate.C69, rate.C72, rate.C74, rate.C77, rate.C80, rate.N10]).toEqual(nulls(11))
    const threshold = run({ C22: null })
    expect([threshold.C24, threshold.C34, threshold.C42, threshold.C62, threshold.C69, threshold.C72, threshold.C77, threshold.C80]).toEqual(nulls(8))
    // Ohne TE gibt es keine Aufteilung für Zeitraum 1; die Summe 0 der Vorlage ist ein Wert ohne Grundlage.
    expect(threshold.C44).toBeNull()
    expect(template({ C22: null }).C44).toBe(0)
  })

  it('fehlt der Buchwert einer belegten Schicht, bleibt die Hochrechnung offen', () => {
    for (const input of ['F12', 'F58']) {
      const results = run({ [input]: null })
      expect([results.F89, results.C89, results.C92, results.C96, results.C100, results.C102, results.N5, results.N11], input).toEqual(nulls(8))
      expect(results.D89, input).toBeGreaterThan(0)
      expect(results.C93, input).toBeGreaterThan(0)
    }
  })

  it('eine Gesamtfehlerquote über der Schwelle wird auch bei offener Genauigkeit gewürdigt', () => {
    expect(run({ C25: null, D50: 60000, E50: 31000, D85: 45000 }).C102).toBe('✖ Gesamtfehlerquote über der Wesentlichkeitsschwelle')
  })

  it('nur Zeitraum 1 ausgefüllt: Umfänge für Zeitraum 1, aber kein Ergebnis für das Geschäftsjahr allein aus Zeitraum 1', () => {
    const inputs: Inputs = { ...sample, C53: null, C54: null, C55: null, C82: null }
    for (const column of ['D', 'E', 'F']) for (const row of ['57', '58', '59', '84', '85', '86', '87']) inputs[`${column}${row}`] = null
    const results = sheet.compute(inputs, context)
    expect([results.C42, results.C44, results.C45, results.C77, results.C78, results.C80, results.C81]).toEqual([50, 28, 26, null, 28, null, null])
    expect(results.D89).toBeCloseTo(57960, 4)
    expect([results.C57, results.C58, results.C61, results.C89, results.C90, results.C92, results.C93, results.C96, results.C100, results.C102, results.N4, results.N5, results.N7, results.N10, results.N11]).toEqual(nulls(15))
    // Die Vorlage rechnet mit den Summen 0 des leeren Zeitraums 2 weiter und zeigt ein Ergebnis allein aus Zeitraum 1.
    const shown = sheet.compute(inputs, likeTemplate)
    expect([shown.C77, shown.C80]).toEqual([0, 32])
    expect(shown.C89).toBeCloseTo(57960 + 36945.054945 + 21125, 4)
    expect(shown.C93).toBeGreaterThan(0)
  })
})

describe('Blatt 11_SRS_2Z_S: Richtlinie für fehlende Angaben', () => {
  /** Zellen, die das leere Formular zeigen darf – alles andere wäre ein Wert ohne Eingabe. */
  const ALLOWED_WHEN_EMPTY: Record<string, CellValue> = {
    N3: 'Einfaches Zufallsstichprobenverfahren, 2 Zeiträume, geschichtet', // fester Text
    C23: '✔ ≤ 2 %', // Prüfhinweis zur Vorgabe 2 %
    C38: 'Nicht angewandt – Anh. I und II gelten', // Vorgabe „Nein“
    C40: 30, // Mindestumfang der Verordnung; das Feld bezeichnet die Untergrenze selbst
    C91: 0, N6: 0, N8: 0, N9: 0, // freiwillige Einzelbeträge: leer heißt „keine“
  }
  /** Zeilen, die für nicht belegte Schichten wie in der Vorlage 0 tragen (Hilfszeilen und Hochrechnung je Schicht). */
  const ZERO_ROWS = ['31', '66', '67', '70', '89', '90']

  it('leeres Formular: keine Summe, kein Umfang, kein Prüfhinweis ohne Eingabe', () => {
    const inputs = defaultInputs(sheet.definition)
    const evaluation = evaluateSheet(sheet, inputs, context)
    const shown = Object.entries(evaluation.cells).filter(([cell, value]) => value !== null && !(cell in inputs))
    const strata = shown.filter(([cell]) => !/^[CN]\d+$/.test(cell))
    expect(Object.fromEntries(shown.filter(([cell]) => /^[CN]\d+$/.test(cell)))).toEqual(ALLOWED_WHEN_EMPTY)
    expect(strata.every(([cell, value]) => value === 0 && ZERO_ROWS.includes(cell.replace(/^[A-Z]+/, '')))).toBe(true)
    expect(evaluation.assumed).toEqual([])
    // Nichts fehlt, was die Vorlage nicht auch erst mit Eingaben zeigte – außer den Beträgen, die sie aus der Vorgabe 2 % und 0 € bildet.
    expect([...evaluation.lacking.keys()]).toEqual([])
    expect(buildSummary(sheet, inputs, evaluation.cells, context, t)).toMatchObject({ primaryValue: '', primaryUnit: '' })
    // Die Vorlage zeigt dagegen 0 Einheiten und viele Summen 0.
    expect(sheet.compute(inputs, likeTemplate)).toMatchObject({ C11: 0, C15: 0, C44: 0, C77: 0, C80: 0, N4: 0, N10: 0 })
  })

  it('Pflichteingabe (requiredInput): „Angabe fehlt“ mit Nennung der Eingabe; wie die Vorlage mit 0 gerechnet und ausgewiesen', () => {
    const inputs = { ...sample, C25: null }
    const current = evaluateSheet(sheet, inputs, context)
    expect([current.cells.C26, current.cells.C34, current.cells.C80]).toEqual(nulls(3))
    expect(current.lacking.get('C26')).toEqual(['C25'])
    expect(current.lacking.get('C34')).toContain('C25')
    const shown = evaluateSheet(sheet, inputs, likeTemplate)
    expect([shown.cells.C26, shown.cells.C34, shown.cells.C42]).toEqual([0, 21, 26])
    expect(shown.lacking.size).toBe(0)
    expect(shown.assumed.find((entry) => entry.input === 'C25')?.cells).toContain('C34')
    // Auch ab der achten Schicht: fehlt σ der Schicht AA, bleibt der Gesamtumfang offen und die Eingabe ist genannt.
    const eighth = { ...moved(sample, 'D', 'AA'), AA29: null }
    expect(evaluateSheet(sheet, eighth, context).lacking.get('C34')).toContain('AA29')
    expect(evaluateSheet(sheet, eighth, context).lacking.get('AA31')).toEqual(['AA29'])
  })

  it('Standardabweichung der Stichprobe (sampleDeviation): mit 0 gerechnet und ausgewiesen', () => {
    const current = evaluateSheet(sheet, { ...sample, E87: null }, context)
    expect(current.cells.C93).toBeGreaterThan(0)
    expect(current.assumed).toEqual([{ input: 'E87', cells: ['E90', 'C90', ...PRECISION_CELLS] }])
    expect(current.lacking.size).toBe(0)
  })

  it('Fehlersumme einer Schicht fehlt, eine andere trägt eine (partialErrorSum): Ergebnis wie die Vorlage, ausgewiesen', () => {
    const cells = ['C89', 'C92', 'C96', 'C97', 'C99', 'C100', 'C101', 'C102', 'N5', 'N11']
    const current = evaluateSheet(sheet, { ...sample, E50: null }, context)
    expect(current.cells.E89).toBeCloseTo((7300000 * 2700) / 560000, 6)
    expect(current.cells.C92).toBeLessThan(run().C92 as number)
    expect(current.assumed).toEqual([{ input: 'E50', cells: ['E89', ...cells], kind: 'partialErrorSum' }])
    expect(current.cells).toEqual(evaluateSheet(sheet, { ...sample, E50: null }, likeTemplate).cells)
    // Zeitraum 2 der Schicht noch nicht geprüft (Σ BV_i und Σ E_i leer): Die Vorlage lässt die ganze Schicht aus der Hochrechnung fallen.
    const unaudited = evaluateSheet(sheet, { ...sample, E84: null, E85: null }, context)
    expect(unaudited.cells.E89).toBeNull()
    expect(unaudited.cells.C89).toBeCloseTo((run().C89 as number) - (run().E89 as number), 6)
    expect(unaudited.assumed).toContainEqual({ input: 'E85', cells, kind: 'partialErrorSum' })
    // Trägt keine Schicht eine Fehlersumme, gibt es kein Ergebnis und nichts auszuweisen.
    const none = evaluateSheet(sheet, { ...sample, D50: null, E50: null, F50: null, D85: null, E85: null, F85: null }, context)
    expect([none.cells.D89, none.cells.C89, none.cells.C92]).toEqual(nulls(3))
    expect(none.assumed).toEqual([])
    expect(none.lacking.size).toBe(0)
  })

  it('Wert ohne Grundlage (withoutBasis): offen ohne „Angabe fehlt“; wie die Vorlage gezeigt', () => {
    const inputs = { ...sample, C25: 0.025, C33: NONE }
    const current = evaluateSheet(sheet, inputs, context)
    expect([current.cells.C44, current.cells.D46, current.cells.D77, current.cells.D79, current.cells.C80, current.cells.C93, current.cells.C102]).toEqual(nulls(7))
    expect(current.lacking.size).toBe(0)
    expect(current.assumed).toEqual([])
    const shown = evaluateSheet(sheet, inputs, likeTemplate).cells
    expect([shown.C44, shown.D46, shown.D77, shown.D79, shown.C80, shown.C93]).toEqual([0, '✔ ≥ 3', 3, '✔ ≥ 3', 16, 0])
    expect(shown.C102).toBe('✔ GFQ und obere Fehlergrenze unter der Schwelle')
    // Mit Gesamtumfang ist die Untergrenze 3 für eine erst in Zeitraum 2 belegte Schicht begründet (Art. 5 Abs. 5).
    expect(run({ G57: 35, G58: 3200000, G59: 11800, C33: NONE }).G77).toBe(3)
  })
})

describe('Blatt 11_SRS_2Z_S: englische Arbeitsübersetzung', () => {
  /** Texte des Rechenkerns und Hinweise der Webfassung, für die eine Übersetzung fehlt. */
  function untranslated(results: Readonly<Record<string, CellValue>>, hints: readonly WebHint[], inputCells: ReadonlySet<string>): string[] {
    const texts = Object.entries(results).flatMap(([cell, value]) => (typeof value === 'string' && !inputCells.has(cell) ? [value] : []))
    const known = { ...shared, ...en.values }
    return [...texts.filter((text) => !(text in known)), ...hints.map((hint) => hint.id).filter((id) => !en.webHints?.[id])]
  }

  it('jede Feldzelle, jeder Abschnitt und die Ergebnisspalte sind übersetzt', () => {
    for (const section of sheet.definition.sections) expect(en.sections?.[section.id]?.title, section.id).toBeTruthy()
    for (const field of fieldsOf(sheet.definition)) {
      const texts = en.fields?.[field.cell]
      for (const key of ['label', 'hint', 'formula', 'interpretation'] as const) expect(Boolean(texts?.[key]), `${field.cell} ${key}`).toBe(Boolean(field[key]))
    }
    expect([en.title, en.shortTitle, en.legalBasis, en.summary?.primary, en.summary?.unit].every(Boolean)).toBe(true)
    expect(Object.keys(en.summary?.rows ?? {})).toEqual(sheet.definition.summary.rows.map((row) => row.cell))
  })

  it('jeder Text, den der Rechenkern in den Golden-Fällen liefert, und jeder Hinweis der Webfassung ist übersetzt', () => {
    const inputCells = new Set(inputFields(sheet.definition).flatMap(cellsOf))
    const missing = new Set<string>()
    for (const golden of loadGolden(sheet.id)) {
      const inputs = caseInputs(sheet, golden)
      for (const policy of [context, likeTemplate]) {
        const results = sheet.compute(inputs, policy)
        for (const text of untranslated(results, sheet.webHints?.(inputs, results, policy) ?? [], inputCells)) missing.add(text)
      }
    }
    expect([...missing]).toEqual([])
  })
})
