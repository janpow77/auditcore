import { describe, expect, it } from 'vitest'
import { createTranslate } from '../src/i18n/messages'
import { cellsOf, defaultInputs, fieldsOf, findField, inputFields, named } from '../src/model/definition'
import { TEMPLATE_POLICY } from '../src/model/policy'
import { subsampleTargets } from '../src/model/list'
import { SUMMARY_CELLS, createContext, summaryOf } from '../src/model/sheet'
import { STRATA_COLUMNS } from '../src/model/strata'
import type { CellValue } from '../src/model/types'
import { sheet } from '../src/sheets/11_SRS_2Z_S/index'
import { INCREASE_INTERPRETATION } from '../src/sheets/shared/srs'
import { strataRows } from '../src/view/sheetView'
import { buildSummary } from '../src/view/summaryView'

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
