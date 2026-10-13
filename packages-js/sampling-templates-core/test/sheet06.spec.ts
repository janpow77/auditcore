import { describe, expect, it } from 'vitest'
import { createTranslate } from '../src/i18n/messages'
import { defaultInputs, fieldsOf, findField, inputCells, named } from '../src/model/definition'
import { evaluateSheet } from '../src/model/evaluate'
import { STRICT_POLICY, TEMPLATE_POLICY } from '../src/model/policy'
import { SUMMARY_CELLS, createContext, localizeSheet, summaryOf, type AvailableSheet } from '../src/model/sheet'
import { STRATA_COLUMNS, TEMPLATE_STRATA } from '../src/model/strata'
import type { SheetTexts } from '../src/model/texts'
import type { CellValue } from '../src/model/types'
import { sheet as sheet04 } from '../src/sheets/04_MUS_1Z_S/index'
import { en as texts04 } from '../src/sheets/04_MUS_1Z_S/texts.en'
import { sheet } from '../src/sheets/06_MUS_2Z_S/index'
import { buildSections, strataRows } from '../src/view/sheetView'
import { loadGolden, sameValue } from './golden'

const context = createContext()
const GLOBAL = 'Global (Art. 5 Abs. 6 Buchst. b)'
const INCREASE = 'Erhöhung bei begrenztem Umfang (Art. 5 Abs. 7 UAbs. 4 Buchst. a)'
const likeTemplate = createContext({ policy: TEMPLATE_POLICY })
const strict = createContext({ policy: STRICT_POLICY })
const sample = (changes: Record<string, CellValue> = {}): Record<string, CellValue> => ({ ...sheet.sample.inputs, ...changes })
const compute = (changes: Record<string, CellValue> = {}): Readonly<Record<string, CellValue>> => sheet.compute(sample(changes), context)
/** Eingaben des Beispiels ohne die genannten Schichtzeilen. */
const withoutRows = (...rows: number[]): Record<string, CellValue> => Object.fromEntries(Object.entries(sheet.sample.inputs).filter(([cell]) => cell.startsWith('C') || !rows.includes(Number(cell.replace(/^[A-Z]+/, '')))))
/** Berechnete Zellen mit einem Wert (ohne Eingabezellen). */
function shown(cells: Readonly<Record<string, CellValue>>): Record<string, CellValue> {
  const inputs = inputCells(sheet.definition)
  return Object.fromEntries(Object.entries(cells).filter(([cell, value]) => value !== null && !inputs.includes(cell)))
}
/** Hilfszeilen, die wie in der Vorlage für unbelegte Schichten 0 tragen. */
const ZERO_ROWS = [26, 60, 61, 64, 86, 87, 88]
const idleZeros = Object.fromEntries(ZERO_ROWS.flatMap((row) => STRATA_COLUMNS.map((column) => [`${column}${row}`, 0])))
/** Zellen der Ergebnisse, die von der Summe der Fehlerquoten einer Schicht abhängen (ohne die Zelle der Schicht in Zeile 87). */
const ERROR_CELLS = ['C87', 'C89', 'C93', 'C94', 'C96', 'C97', 'C98', 'C99', 'N5', 'N11']
/** Prüft eine englische Arbeitsübersetzung gegen Definition und Golden-Fälle eines Blatts. */
function expectTranslated(target: AvailableSheet, texts: SheetTexts | undefined): void {
  const fields = fieldsOf(target.definition)
  expect(fields.filter((field) => !texts?.fields?.[field.cell]?.label).map((field) => field.cell)).toEqual([])
  expect(fields.filter((field) => field.hint && !texts?.fields?.[field.cell]?.hint).map((field) => field.cell)).toEqual([])
  expect(fields.filter((field) => field.interpretation && !texts?.fields?.[field.cell]?.interpretation).map((field) => field.cell)).toEqual([])
  expect(Object.keys(texts?.fields ?? {}).filter((cell) => !fields.some((field) => field.cell === cell))).toEqual([])
  expect(target.definition.sections.filter((section) => !texts?.sections?.[section.id]?.title || (section.reference && !texts.sections[section.id]?.reference)).map((section) => section.id)).toEqual([])
  expect(target.definition.summary.rows.filter((row) => !texts?.summary?.rows?.[row.cell]).map((row) => row.cell)).toEqual([])
  const produced = new Set(loadGolden(target.id).flatMap((golden) => Object.values(golden.erwartet).filter((value): value is string => typeof value === 'string')))
  expect([...produced].filter((value) => !texts?.values?.[value])).toEqual([])
}
/** Eingaben einer Schichtspalte in eine andere Spalte verschieben. */
function moveStratum(inputs: Readonly<Record<string, CellValue>>, from: string, to: string): Record<string, CellValue> {
  return Object.fromEntries(Object.entries(inputs).map(([cell, value]) => [/^[A-Z]+/.exec(cell)?.[0] === from ? `${to}${cell.slice(from.length)}` : cell, value]))
}

describe('Blatt 06_MUS_2Z_S', () => {
  it('Beispielwerte mit drei Schichten', () => {
    const results = compute()
    expect(results).toMatchObject({ C8: 26000000, C9: 23500000, C11: 49500000, C29: 90, C35: 90, C37: 49, C38: 44, D37: 22, E37: 17, F37: 10, G37: null })
    expect(results).toMatchObject({ C63: 21, C69: 22, D69: 10, C70: 49, N10: 71, D45: '✔ ≥ 3', D79: '✔ ≥ 3', C72: '✔ ≥ 30 Einheiten', N3: 'MUS-Standardansatz, 2 Zeiträume, geschichtet' })
    const result = named(sheet.definition, results)
    expect(result.projectedError).toBeCloseTo(460599.21, 2)
    expect(result.precision).toBeCloseTo(263808.15, 2)
    expect(result.totalErrorRate).toBeCloseTo(0.0091753, 7)
    expect(result.assessment).toBe('✔ GFQ und obere Fehlergrenze unter der Schwelle')
  })

  it('jede Zelle und jeder Alias kommt genau einmal vor; Schichtzeilen lösen sich je Spalte auf', () => {
    const fields = fieldsOf(sheet.definition)
    expect(new Set(fields.map((field) => field.cell)).size).toBe(fields.length)
    expect(new Set(fields.map((field) => field.alias)).size).toBe(fields.length)
    for (const field of fields) expect(field.alias).toMatch(/^[a-z][A-Za-z0-9]*$/)
    expect(findField(sheet.definition, 'AM83')?.alias).toBe('stratumSampleDeviationPeriod2')
    expect(findField(sheet.definition, 'C69')?.cell).toBe('D69')
    expect(strataRows(sheet)).toEqual(['8', '9', '10', '24', '25', '41', '42', '47', '48', '49', '51', '52', '53', '75', '76', '81', '82', '83'])
  })

  it('der Rechenkern füllt jede Zelle der Definition, jede Schichtspalte und die Ergebnisübersicht', () => {
    for (const inputs of [sheet.sample.inputs, {}]) {
      const cells = Object.keys(sheet.compute(inputs, context))
      for (const field of fieldsOf(sheet.definition)) {
        for (const cell of field.columns ? STRATA_COLUMNS.map((column) => `${column}${field.cell.slice(1)}`) : [field.cell]) expect(cells).toContain(cell)
        if (field.total) expect(cells).toContain(field.total)
      }
      for (const cell of Object.values(SUMMARY_CELLS)) expect(cells).toContain(cell)
    }
  })

  it('Vorgaben der Vorlage und Beispielwerte', () => {
    expect(defaultInputs(sheet.definition)).toEqual({ C14: 'zweiseitig', C17: 0.02, C28: 'Standard (Art. 5 Abs. 6 Buchst. a)', C31: 'Nein', C32: 'Nein' })
    const cells = inputCells(sheet.definition)
    for (const cell of Object.keys(sheet.sample.inputs)) expect(cells).toContain(cell)
  })

  it('die achte Schicht (Spalte AA) rechnet wie eine Schicht der Vorlage', () => {
    const moved = sheet.compute(moveStratum(sheet.sample.inputs, 'F', 'AA'), context)
    const original = compute()
    for (const [cell, value] of Object.entries(original)) {
      const column = /^[A-Z]+/.exec(cell)?.[0]
      if (column === 'F') expect(sameValue(value, moved[`AA${cell.slice(1)}`] ?? null), cell).toBe(true)
      else if (column !== 'AA') expect(sameValue(value, moved[cell] ?? null), cell).toBe(true)
    }
    expect(moved.F37).toBeNull()
    expect(moved.F86).toBe(0)
    const hints = sheet.webHints?.(moveStratum(sheet.sample.inputs, 'F', 'AA'), moved, context).map((hint) => hint.id)
    expect(hints).toContain('strata-beyond-template')
    expect(sheet.webHints?.(sheet.sample.inputs, original, context).map((hint) => hint.id)).not.toContain('strata-beyond-template')
  })

  it('zwanzig Schichten: Summen laufen über alle Spalten', () => {
    const inputs: Record<string, CellValue> = { ...sheet.sample.inputs }
    for (const column of STRATA_COLUMNS) Object.assign(inputs, moveStratum(Object.fromEntries(Object.entries(sheet.sample.inputs).filter(([cell]) => cell.startsWith('D'))), 'D', column))
    const results = sheet.compute(inputs, context)
    expect(results.C8).toBe(20 * 12000000)
    expect(results.C37).toBe(STRATA_COLUMNS.reduce((sum, column) => sum + (results[`${column}37`] as number), 0))
    expect(results.C69).toBe(20 * (results.D69 as number))
    expect([results.AM69, results.AM79, results.AM88]).toEqual([results.D69, results.D79, results.D88])
    expect(typeof results.C97).toBe('number')
  })

  it('der Ansatz der Neuberechnung wählt den Umfang je Schicht für Zeitraum 2', () => {
    expect(compute()).toMatchObject({ D69: 10, E69: 8, F69: 4, D70: 22 })
    const global = compute({ C28: GLOBAL })
    expect(global).toMatchObject({ D70: (global.D37 as number) + (global.D68 as number), C66: 47 })
    expect(compute({ C28: INCREASE })).toMatchObject({ D69: 21, E69: 16, F69: 9 })
    expect(compute({ C28: 'keine Neuberechnung' })).toMatchObject({ D69: 20, E69: 15, F69: 9 })
  })

  it('Schicht ohne Prognose für Zeitraum 2: Die Untergrenze 3 der Vorlage ist ein Wert ohne Grundlage, die Schichtnummer steht im Hinweis', () => {
    // MAX übergeht in der Vorlage den leeren Planumfang; es bliebe die Untergrenze 3.
    const inputs = sample({ C28: 'keine Neuberechnung', F9: null, F25: null })
    const current = evaluateSheet(sheet, inputs, context)
    expect(current.cells).toMatchObject({ D69: 22, E69: 16, F38: null, F69: null, F78: null, F79: null, C69: null, C89: null, N10: null })
    expect(current.lacking.has('F69')).toBe(false)
    expect(evaluateSheet(sheet, inputs, likeTemplate).cells).toMatchObject({ F69: 3, F78: 3, F79: '✔ ≥ 3', C69: 41, N10: 93 })
    const hints = sheet.webHints?.(inputs, current.cells, context) ?? []
    expect(hints.find((hint) => hint.id === 'no-planned-size-3')?.text).toMatch(/^Schicht 3: /)
    expect(hints.filter((hint) => hint.id.startsWith('no-planned-size')).map((hint) => hint.id)).toEqual(['no-planned-size-3'])
    // Beim Standardansatz kommt der Umfang der Schicht aus der Neuberechnung, nicht aus dem Planumfang.
    expect(typeof compute({ F9: null, F25: null }).F69).toBe('number')
  })

  it('negativer Nenner: kein Umfang für Zeitraum 2, weder Prüfhinweis noch Hochrechnung ohne Grundlage, Hinweis der Webfassung', () => {
    const inputs = sample({ D49: 0.9, E49: 0.9, F49: 0.9 })
    const results = sheet.compute(inputs, context)
    expect(results).toMatchObject({ C63: '✖ nicht anwendbar (Nenner ≤ 0)', D69: null, C69: null, C72: null, D78: null, D79: null, C87: null, C89: null, N10: null })
    // Die Vorlage zeigt „✔ ≥ 3“ ohne Einheiten, die Summe 0 und als EE nur die Fehler der hochwertigen Einheiten.
    expect(sheet.compute(inputs, likeTemplate)).toMatchObject({ D69: null, C69: 0, D79: '✔ ≥ 3', C87: 0, C89: 9500, N10: 49 })
    expect(sheet.webHints?.({}, results, context).map((hint) => hint.id)).toContain('negative-denominator')
    expect(compute({ D49: 0.9, E49: 0.9, F49: 0.9, C28: GLOBAL }).C69).toBeGreaterThan(0)
  })

  it('Auslegung der Vorlage: die Auswahl des Ansatzes und die Zeile mit der Erhöhung sind gekennzeichnet', () => {
    const marked = fieldsOf(sheet.definition).filter((field) => field.interpretation)
    expect(marked.map((field) => field.cell)).toEqual(['C28', 'D69'])
    expect(marked[0]?.interpretation).toContain('Art. 5 Abs. 7 UAbs. 4 Buchst. a')
  })

  it('fehlt die Standardabweichung einer belegten Schicht, bleiben Umfang und Folgegrößen offen', () => {
    expect(compute({ E24: null })).toMatchObject({ E26: null, C26: null, C27: null, C29: null, C35: null, D37: null, C37: null, D45: null, C97: null })
    expect(compute({ F53: null })).toMatchObject({ F61: null, C61: null, C63: null, D69: null, C69: null, C35: 90, D37: 22 })
    // Schicht ohne Buchwert im zweiten Zeitraum: Ihre Standardabweichung wird nicht verlangt.
    const withoutSecond = compute({ F51: null, F52: null, F53: null, F75: null, F76: null, F81: null, F82: null, F83: null })
    expect(withoutSecond).toMatchObject({ F61: 0, F69: null, F79: null })
    expect(withoutSecond.C69).toBeGreaterThan(0)
    const current = evaluateSheet(sheet, sample({ E24: null }), context)
    expect(current.lacking.get('C35')).toEqual(['E24'])
    expect(current.lacking.get('E26')).toEqual(['E24'])
    expect(typeof evaluateSheet(sheet, sample({ E24: null }), likeTemplate).cells.C35).toBe('number')
  })

  it('leeres Formular: keine Summe 0, kein Buchwert 0, kein Umfang 0 – nur feste Texte, die Prüfung der Vorgabe 2 % und die Nullen der Hilfszeilen', () => {
    const fixed = { C33: 'Nicht angewandt – Anh. I und II gelten', N3: 'MUS-Standardansatz, 2 Zeiträume, geschichtet', N8: 0, N9: 0, ...idleZeros }
    expect(shown(evaluateSheet(sheet, defaultInputs(sheet.definition), context).cells)).toEqual({ ...fixed, C18: '✔ ≤ 2 %' })
    expect(shown(evaluateSheet(sheet, {}, context).cells)).toEqual(fixed)
    expect(sheet.webHints?.({}, sheet.compute({}, context), context)).toEqual([])
    // Die Vorlage zeigt dort Summen, Buchwerte und einen Stichprobenumfang von 0.
    expect(evaluateSheet(sheet, {}, likeTemplate).cells).toMatchObject({ C8: 0, C11: 0, C37: 0, C51: 0, C55: 0, C69: 0, C86: 0, C87: 0, N4: 0, N6: 0, N10: 0 })
    // Begrenzter Umfang ohne rechnerischen Umfang: kein anzuwendender Umfang von 50 Einheiten.
    const limited = { ...defaultInputs(sheet.definition), C30: 2, C32: 'Ja' }
    expect(evaluateSheet(sheet, limited, context).cells).toMatchObject({ C34: 50, C35: null, C66: null })
    expect(evaluateSheet(sheet, limited, likeTemplate).cells).toMatchObject({ C35: 50, C66: 50 })
    expect(sheet.webHints?.(limited, sheet.compute(limited, context), context).map((hint) => hint.id)).toEqual(['limited-size-open'])
  })

  it('zweiter Zeitraum leer: keine Ergebnisse allein aus dem ersten Zeitraum', () => {
    const firstOnly = withoutRows(51, 52, 53, 75, 76, 81, 82, 83)
    const current = evaluateSheet(sheet, firstOnly, context)
    expect(current.cells).toMatchObject({ C35: 90, C37: 49, C70: 49, C51: null, C55: null, C63: null, C69: null, C87: null, C88: null, C89: null, C90: null, C97: null, C99: null, N4: null, N5: null, N7: null, N10: null, N11: null })
    expect(current.lacking.has('C89')).toBe(false)
    // Die Vorlage rechnet mit einem Buchwert des zweiten Zeitraums von 0 € weiter und zeigt eine Gesamtfehlerquote.
    const template = evaluateSheet(sheet, firstOnly, likeTemplate).cells
    expect(template).toMatchObject({ C51: 0, C55: 26000000, C63: 0, C69: 0, N10: 49 })
    expect(typeof template.C97).toBe('number')
    expect(sheet.webHints?.(firstOnly, current.cells, context).map((hint) => hint.id)).toContain('second-period-empty')
    // Ohne Prognose für Zeitraum 2 ist schon der Gesamtumfang nicht bestimmt.
    expect(evaluateSheet(sheet, withoutRows(9, 10, 25), context).cells).toMatchObject({ C9: null, C11: null, C29: null, C35: null, N10: null })
  })

  it('fehlt die Standardabweichung der Stichprobe einer Schicht, ist ihr Beitrag 0 und wird ausgewiesen', () => {
    const shared = ['C88', 'C90', 'C93', 'C94', 'C95', 'C98', 'C99']
    expect(sheet.zeroAssumed?.(compute())).toEqual([])
    expect(sheet.zeroAssumed?.(compute({ F83: null }))).toEqual([{ input: 'F83', cells: ['F88', ...shared] }])
    const first = compute({ E49: null })
    expect(sheet.zeroAssumed?.(first)).toEqual([{ input: 'E49', cells: ['E88', ...shared] }])
    // Ersatzweise σ_rh für die Neuberechnung
    expect(first.E59).toBe(0.14)
    expect(sheet.zeroAssumed?.(compute({ D49: null, D83: null })).map((entry) => entry.input)).toEqual(['D49', 'D83'])
    const moved = moveStratum({ ...sheet.sample.inputs, F49: null }, 'F', 'AA')
    expect(sheet.zeroAssumed?.(sheet.compute(moved, context)).map((entry) => entry.input)).toEqual(['AA49'])
    const open = evaluateSheet(sheet, sample({ F83: null }), strict)
    expect(open.cells).toMatchObject({ F88: null, C90: null, C98: null })
    expect(open.lacking.get('C90')).toEqual(['F83'])
    expect(evaluateSheet(sheet, sample({ F83: null }), context).lacking.size).toBe(0)
  })

  it('Summe der Fehlerquoten einer Schicht fehlt, eine andere ist eingetragen: wie die Vorlage mit 0 gerechnet und ausgewiesen', () => {
    for (const [input, stratum] of [['E48', 'E87'], ['F82', 'F87']] as const) {
      const current = evaluateSheet(sheet, sample({ [input]: null }), context)
      expect(current.assumed).toEqual([{ input, cells: [stratum, ...ERROR_CELLS], kind: 'partialErrorSum' }])
      expect(current.lacking.size).toBe(0)
      expect(typeof current.cells.C89).toBe('number')
      expect(evaluateSheet(sheet, sample({ [input]: null }), likeTemplate).cells.C89).toBe(current.cells.C89)
      const open = evaluateSheet(sheet, sample({ [input]: null }), strict)
      expect(open.cells).toMatchObject({ [stratum]: null, C87: null, C89: null, C97: null, C99: null, N5: null, N11: null })
      expect(open.lacking.get('C89')).toEqual([input])
    }
    // Ein ganzer Zeitraum ohne Summe der Fehlerquoten: je belegter Schicht ein Ausweis.
    expect(evaluateSheet(sheet, withoutRows(82), context).assumed.map((entry) => entry.input)).toEqual(['D82', 'E82', 'F82'])
    // Die 8. Schicht (Spalte AA) wird ebenso ausgewiesen.
    const moved = moveStratum(sample({ F48: null }), 'F', 'AA')
    expect(sheet.zeroAssumed?.(sheet.compute(moved, context))).toEqual([{ input: 'AA48', cells: ['AA87', ...ERROR_CELLS], kind: 'partialErrorSum' }])
    // Ohne jede Summe der Fehlerquoten zeigt auch die Vorlage keinen extrapolierten Fehler: nichts auszuweisen.
    const none = evaluateSheet(sheet, withoutRows(48, 82), context)
    expect(none.cells.C89).toBeNull()
    expect(none.assumed.filter((entry) => entry.kind === 'partialErrorSum')).toEqual([])
  })

  it('Prüfhinweis „mindestens drei Einheiten“ ohne Einheiten: kein „✔ ≥ 3“; mit Einheiten wie die Vorlage', () => {
    // „TE ≤ AE“: Die Vorlage zeigt keinen Umfang je Schicht und trotzdem „✔ ≥ 3“.
    const current = evaluateSheet(sheet, sample({ C20: 0.025 }), context)
    expect(current.cells).toMatchObject({ C29: 'TE ≤ AE', D37: null, D44: null, D45: null, C37: null })
    expect(current.lacking.has('D45')).toBe(false)
    expect(evaluateSheet(sheet, sample({ C20: 0.025 }), likeTemplate).cells).toMatchObject({ D44: null, D45: '✔ ≥ 3', C37: 0 })
    expect(compute({ D41: 21 })).toMatchObject({ D44: 1, D45: '✖ < 3', E45: '✔ ≥ 3' })
    expect(sheet.deviations.filter((entry) => entry.kind === 'withoutBasis' && /^[A-Z]+45$/.test(entry.cell))).toHaveLength(STRATA_COLUMNS.length * 3)
  })

  it('Hinweise der Webfassung verändern kein Ergebnis', () => {
    const results = compute()
    expect(sheet.webHints?.(sheet.sample.inputs, results, context).map((hint) => hint.id)).toEqual(['strata-sum-exceeds-size'])
    expect(results.C37).toBeGreaterThan(0)
    expect((results.C37 as number) + (results.C38 as number)).toBeGreaterThan(results.C35 as number)
    const firstOnly = Object.fromEntries(Object.entries(sheet.sample.inputs).filter(([cell]) => !/^[D-J](5[123]|7[56]|8[123])$/.test(cell)))
    const hints = sheet.webHints?.(firstOnly, sheet.compute(firstOnly, context), context).map((hint) => hint.id)
    expect(hints).toContain('second-period-empty')
    // Hinweise zu einer Schicht nennen die Schichtnummer und tragen sie in der Kennung.
    const exceeded = { ...sheet.sample.inputs, E52: 5, F52: 2, C13: 0.95 }
    const found = sheet.webHints?.(exceeded, sheet.compute(exceeded, context), context) ?? []
    expect(found.map((hint) => hint.id)).toEqual(['strata-sum-exceeds-size', 'size-exceeds-population-2-2', 'size-exceeds-population-2-3', 'confidence-outside-annex'])
    expect(found[1]?.text).toBe('Schicht 2: Stichprobenumfang für Zeitraum 2 übersteigt die Anzahl der Einheiten der Schicht')
  })

  it('Anzeigemodell und Ergebnisübersicht für Blatt 18', () => {
    const rows = buildSections(sheet, sheet.sample.inputs, compute(), context, createTranslate()).flatMap((section) => [...section.rows])
    const size = rows.find((row) => row.cell === 'D69')
    expect(size?.strata?.cells).toHaveLength(TEMPLATE_STRATA.length + 13)
    expect(size?.interpretation).toContain('Erhöhung')
    expect(summaryOf(sheet.id, compute())).toMatchObject({ sheet: '06_MUS_2Z_S', method: 'MUS-Standardansatz, 2 Zeiträume, geschichtet', bookValue: 50200000, exhaustiveError: 9500, sampleSize: 71 })
  })

  it('unvollständige Belegungen: jeder gezeigte Wert ist der Wert unter der Richtlinie „wie die Vorlage“', () => {
    let seed = 2026101306
    const random = (): number => {
      seed = (seed * 1664525 + 1013904223) % 4294967296
      return seed / 4294967296
    }
    const cells = inputCells(sheet.definition)
    const filled = Object.keys(sheet.sample.inputs)
    for (let run = 0; run < 120; run += 1) {
      const inputs: Record<string, CellValue> = { ...sheet.sample.inputs, C28: context.parameters.lists.recalculation[run % 4]!, C32: run % 3 ? 'Nein' : 'Ja' }
      for (const cell of filled) if (random() < 0.12) inputs[cell] = null
      const results = evaluateSheet(sheet, inputs, context, false).cells
      const template = evaluateSheet(sheet, inputs, likeTemplate).cells
      for (const [cell, value] of Object.entries(results)) {
        if (value !== null && !cells.includes(cell)) expect(sameValue(template[cell] ?? null, value), `${cell} Lauf ${run}`).toBe(true)
      }
    }
  }, 30000)

  it('englische Arbeitsübersetzung: jedes Feld, jede Fundstelle, jeder Abschnitt, jeder Text des Rechenkerns und jeder Hinweis der Webfassung', () => {
    const texts = sheet.translations?.en
    expectTranslated(sheet, texts)
    const firstOnly = withoutRows(51, 52, 53, 75, 76, 81, 82, 83)
    const twenty: Record<string, CellValue> = { ...sheet.sample.inputs, C28: 'keine Neuberechnung' }
    for (const column of STRATA_COLUMNS) Object.assign(twenty, moveStratum(Object.fromEntries(Object.entries(sheet.sample.inputs).filter(([cell]) => cell.startsWith('D'))), 'D', column), { [`${column}9`]: null, [`${column}52`]: 1 })
    const cases = [sample({ D49: 0.9, E49: 0.9, F49: 0.9 }), firstOnly, sample({ C13: 0.95 }), { C30: 2, C32: 'Ja' }, twenty, { ...twenty, C28: 'Standard (Art. 5 Abs. 6 Buchst. a)', D9: 11000000, D25: 0.1 }]
    const hints = cases.flatMap((inputs) => sheet.webHints?.(inputs, sheet.compute(inputs, context), context) ?? [])
    expect(new Set(hints.map((hint) => hint.id))).toEqual(new Set(Object.keys(texts?.webHints ?? {})))
    expect(texts?.webHints?.['no-planned-size-20']).toMatch(/^Stratum 20: /)
    expect(localizeSheet(sheet, 'en').definition.title).toBe('MUS standard approach – two periods, stratified')
  })
})

describe('Blatt 04_MUS_1Z_S: englische Arbeitsübersetzung (noch nicht am Blatt angemeldet)', () => {
  it('jedes Feld, jede Fundstelle, jeder Abschnitt, jeder Text des Rechenkerns und jeder Hinweis der Webfassung', () => {
    expectTranslated(sheet04, texts04)
    const inputs: Record<string, CellValue> = { ...sheet04.sample.inputs, C13: 0.95, D10: 10, E10: 10, F10: 10 }
    for (const column of STRATA_COLUMNS.slice(3, 8)) Object.assign(inputs, { [`${column}9`]: 1000000, [`${column}24`]: 0.1 })
    const hints = sheet04.webHints?.(inputs, sheet04.compute(inputs, context), context) ?? []
    expect(new Set(hints.map((hint) => hint.id))).toEqual(new Set(Object.keys(texts04.webHints ?? {})))
    expect(localizeSheet({ ...sheet04, translations: { en: texts04 } }, 'en').definition.title).toBe('MUS standard approach – one period, stratified')
  })
})
