import { describe, expect, it } from 'vitest'
import { createTranslate } from '../src/i18n/messages'
import { cellsOf, defaultInputs, fieldsOf, inputFields, named } from '../src/model/definition'
import { evaluateSheet } from '../src/model/evaluate'
import { STRICT_POLICY, TEMPLATE_POLICY } from '../src/model/policy'
import { SUMMARY_CELLS, createContext, localizeSheet, summaryOf, type AvailableSheet } from '../src/model/sheet'
import { EXTRA_STRATA, STRATA_COLUMNS, TEMPLATE_STRATA } from '../src/model/strata'
import type { CellValue } from '../src/model/types'
import { sheet as sheet13 } from '../src/sheets/13_NS_GW/index'
import { sheet as sheet14 } from '../src/sheets/14_NS_GW_S/index'
import { sheet as sheet15 } from '../src/sheets/15_NS_PPS/index'
import { sheet as sheet16 } from '../src/sheets/16_NS_PPS_S/index'
import { checkAdmissibility, checkCoverage, minimumCoverage, stratumSampleSize } from '../src/sheets/shared/nonstatistical'
import { buildSummary } from '../src/view/summaryView'
import { compareCase, loadGolden } from './golden'
import { officialWording } from '../src/model/terms'

const context = createContext()
const t = createTranslate()
const SHEETS: readonly AvailableSheet[] = [sheet13, sheet14, sheet15, sheet16]
const run = (sheet: AvailableSheet, changes: Record<string, CellValue> = {}): Record<string, CellValue> => sheet.compute({ ...sheet.sample.inputs, ...changes }, context)
const hintIds = (sheet: AvailableSheet, inputs: Record<string, CellValue>): string[] => (sheet.webHints?.(inputs, sheet.compute(inputs, context), context) ?? []).map((hint) => hint.id)
const template = createContext({ policy: TEMPLATE_POLICY })
const strict = createContext({ policy: STRICT_POLICY })
/** Beispielwerte mit Änderungen, ausgewertet unter der Richtlinie des Kontexts. */
const evaluate = (sheet: AvailableSheet, changes: Record<string, CellValue>, policy = context): ReturnType<typeof evaluateSheet> => evaluateSheet(sheet, { ...sheet.sample.inputs, ...changes }, policy)

/**
 * Zellen, die das leere Formular zeigen darf: die Vorgabe der Signifikanzschwelle,
 * feste Texte (N3, N7), die freiwilligen Einzelbeträge (Fehler der umfassenden Schicht
 * bzw. der hochwertigen Einheiten aus `N(...)`, N6, N8, N9) und in den geschichteten
 * Blättern die Zeile des extrapolierten Fehlers je Schicht, die in der Vorlage für
 * unbelegte Schichten 0 trägt (`IF(D11="";0;…)`).
 */
const EMPTY_FORM: Readonly<Record<string, readonly string[]>> = {
  '13_NS_GW': ['C27', 'C20', 'N3', 'N6', 'N7', 'N8', 'N9'],
  '14_NS_GW_S': ['C34', 'C28', 'N3', 'N6', 'N7', 'N8', 'N9', ...STRATA_COLUMNS.map((column) => `${column}27`)],
  '15_NS_PPS': ['C31', 'C24', 'N3', 'N6', 'N7', 'N8', 'N9'],
  // C19, C20, C25, C29, N6: Summen der freiwilligen hochwertigen Einheiten, wie in der Vorlage 0 (Entscheidung des Inhabers vom 17.10.2026).
  '16_NS_PPS_S': ['C19', 'C20', 'C25', 'C29', 'C35', 'N3', 'N6', 'N7', 'N8', 'N9', ...STRATA_COLUMNS.map((column) => `${column}28`)],
}

describe.each(SHEETS)('Nichtstatistische Blätter: $id', (sheet) => {
  it('jede Zelle und jeder Alias kommt genau einmal vor', () => {
    const fields = fieldsOf(sheet.definition)
    expect(new Set(fields.map((field) => field.cell)).size).toBe(fields.length)
    expect(new Set(fields.map((field) => field.alias)).size).toBe(fields.length)
    for (const field of fields) expect(field.alias).toMatch(/^[a-z][A-Za-z0-9]*$/)
  })

  it('der Rechenkern füllt jede Zelle der Definition und die Ergebnisübersicht', () => {
    const cells = Object.keys(run(sheet))
    for (const field of fieldsOf(sheet.definition)) {
      for (const cell of cellsOf(field)) expect(cells).toContain(cell)
      if (field.total) expect(cells).toContain(field.total)
    }
    for (const cell of Object.values(SUMMARY_CELLS)) expect(cells).toContain(cell)
  })

  it('Beispielwerte belegen nur Eingabezellen und ergeben ein vollständiges Ergebnis', () => {
    const cells = inputFields(sheet.definition).flatMap(cellsOf)
    for (const cell of Object.keys(sheet.sample.inputs)) expect(cells).toContain(cell)
    const summary = summaryOf(sheet.id, run(sheet))
    expect(summary.precision).toBe('n. a. (Art. 8 Abs. 2)')
    expect(summary.totalErrorRate).toBeGreaterThan(0)
    expect(summary.totalErrorRate).toBeLessThan(0.02)
    expect(named(sheet.definition, run(sheet)).assessment).toBe('✔ Gesamtfehlerquote unter der Signifikanzschwelle')
    expect(sheet.webHints?.(sheet.sample.inputs, run(sheet), context).filter((hint) => hint.id !== 'strata-sum-exceeds-size')).toEqual([])
    expect(sheet.zeroAssumed?.(run(sheet)) ?? []).toEqual([])
  })

  it('einzige Vorgabe der Vorlage ist die Signifikanzschwelle von 2 %', () => {
    expect(Object.values(defaultInputs(sheet.definition))).toEqual([0.02])
  })

  it('leeres Formular: kein Prüfhinweis und keine Fehlerquote', () => {
    const results = sheet.compute(defaultInputs(sheet.definition), context)
    const result = named(sheet.definition, results)
    expect([result.checkAdmissibility, result.checkCoverage, result.projectedError, result.totalErrorRate, result.assessment]).toEqual([null, null, null, null, null])
    expect(buildSummary(sheet, defaultInputs(sheet.definition), results, context, t).hints).toEqual([])
  })

  it('leeres Formular zeigt nur die ausdrücklich zulässigen Zellen', () => {
    const evaluation = evaluateSheet(sheet, defaultInputs(sheet.definition), context)
    const shown = Object.entries(evaluation.cells).filter(([, value]) => value !== null && value !== '')
    expect(shown.map(([cell]) => cell).sort()).toEqual([...EMPTY_FORM[sheet.id]!].sort())
    // Außer der Vorgabe und den festen Texten stehen dort nur Nullen.
    expect(shown.filter(([, value]) => typeof value === 'number' && value !== 0).map(([cell]) => cell)).toEqual([sheet.definition.summary.gauge?.threshold])
    expect(evaluation.assumed).toEqual([])
    expect(evaluation.cells[sheet.definition.summary.primary.cell]).toBeNull()
    expect(evaluation.cells.N10).toBeNull()
  })

  it('die Zufallsbelegungen sind vollständig: 100 Fälle ohne jede Abweichung', () => {
    const random = loadGolden(sheet.id).filter((golden) => golden.name.startsWith('Zufall'))
    expect(random.length).toBeGreaterThanOrEqual(100)
    for (const golden of random) {
      const report = compareCase(sheet, golden)
      expect([golden.name, report.explained.length, report.unexplained.length]).toEqual([golden.name, 0, 0])
    }
  })

  it('die englische Arbeitsübersetzung deckt jedes Feld und jeden Text des Rechenkerns ab', () => {
    const texts = sheet.translations?.en
    for (const field of fieldsOf(sheet.definition)) expect(texts?.fields?.[field.cell]?.label, field.cell).toBeTruthy()
    const produced = loadGolden(sheet.id).flatMap((golden) => Object.values(golden.erwartet).filter((value): value is string => typeof value === 'string').map((value) => officialWording(value)))
    for (const value of new Set(produced)) expect(texts?.values?.[value], value).toBeTruthy()
    expect(localizeSheet(sheet, 'en').definition.title).toBe(texts?.title)
  })

  it('die englische Arbeitsübersetzung deckt jeden Hinweis der Webfassung ab, den ein Golden-Fall auslöst', () => {
    const translated = sheet.translations?.en?.webHints ?? {}
    const hints = loadGolden(sheet.id).flatMap((golden) => {
      const inputs = { ...defaultInputs(sheet.definition), ...golden.eingaben }
      return sheet.webHints?.(inputs, sheet.compute(inputs, context), context) ?? []
    })
    for (const hint of hints) expect(translated[hint.id], hint.id).toBeTruthy()
  })
})

describe('Gemeinsame Formeln der Blätter 13–16', () => {
  it('Zulässigkeit: Schwelle bei 300 Einheiten', () => {
    expect(checkAdmissibility(299)).toBe('✔ N < 300: zulässig (Art. 79 Abs. 2 VO (EU) 2021/1060; Art. 6 Abs. 1)')
    expect(checkAdmissibility(300)).toBe('⚠ N ≥ 300: nur im Fall des Art. 6 Abs. 3 zulässig')
    expect(checkAdmissibility(null)).toBeNull()
  })

  it('Mindesterfassung: 10 % aufgerundet, glatte Werte ohne Gleitkommarest', () => {
    expect([30, 70, 180, 181, 290].map(minimumCoverage)).toEqual([3, 7, 18, 19, 29])
    expect(minimumCoverage(null)).toBeNull()
    expect(checkCoverage(18, 18)).toBe('✔ Mindesterfassung erreicht')
    expect(checkCoverage(17, 18)).toBe('✖ Mindesterfassung von 10 % nicht erreicht')
    expect(checkCoverage(null, 18)).toBeNull()
  })

  it('Umfang je Schicht: aufgerundet, mindestens 1, leere Schicht ohne Wert', () => {
    expect(stratumSampleSize(60, 180, 18)).toBe(6)
    expect(stratumSampleSize(50, 150, 10)).toBe(4)
    expect(stratumSampleSize(2, 176, 12)).toBe(1)
    expect(stratumSampleSize(80, 176, 0)).toBe(1)
    expect(stratumSampleSize(null, 176, 12)).toBeNull()
    expect(stratumSampleSize(80, 176, null)).toBeNull()
    expect(stratumSampleSize(0, 0, 12)).toBeNull()
  })
})

describe('Blatt 13 und 15: Verknüpfung mit Blatt 02 und Hinweise der Webfassung', () => {
  it.each([sheet13, sheet15])('$id: Buchwert und Anzahl kommen aus Blatt 02, solange sie nicht überschrieben sind', (sheet) => {
    const linked = createContext({ sheets: { '02_Grundgesamtheit': { C51: 1000000, C52: 100 } } })
    const minimum = named(sheet.definition, sheet.compute(defaultInputs(sheet.definition), linked))
    expect(minimum).toMatchObject({ bookValue: 1000000, populationSize: 100, minimumCoverage: 10 })
    expect(named(sheet.definition, sheet.compute({ ...defaultInputs(sheet.definition), C8: 320 }, linked))).toMatchObject({ bookValue: 1000000, populationSize: 320, minimumCoverage: 32, checkAdmissibility: '⚠ N ≥ 300: nur im Fall des Art. 6 Abs. 3 zulässig' })
  })

  it('Stichprobenumfang über der Anzahl der Einheiten', () => {
    expect(hintIds(sheet13, { ...sheet13.sample.inputs, C13: 200 })).toEqual(['size-exceeds-population'])
    expect(hintIds(sheet15, { ...sheet15.sample.inputs, C10: 200 })).toEqual(['size-exceeds-population'])
  })

  it('Blatt 13: ohne Umfang der Zufallsstichprobe bleibt die Gesamtstichprobe offen', () => {
    const results = run(sheet13, { C13: null })
    expect([results.C14, results.C16, results.N10]).toEqual([null, null, null])
    expect(results.C26).toBeGreaterThan(0)
  })

  it.each([
    { sheet: sheet13, input: 'C13', cell: 'C14', shown: 4 },
    { sheet: sheet15, input: 'C10', cell: 'C17', shown: -3 },
  ])('$sheet.id, Pflichteingabe $input fehlt: „Angabe fehlt“ mit Nennung der Eingabe; wie die Vorlage mit 0 gerechnet und ausgewiesen', ({ sheet, input, cell, shown }) => {
    const current = evaluate(sheet, { [input]: null })
    expect([current.cells[cell], current.cells.N10]).toEqual([null, null])
    expect(current.lacking.get(cell)).toEqual([input])
    expect(current.assumed).toEqual([])
    const like = evaluate(sheet, { [input]: null }, template)
    expect(like.cells[cell]).toBe(shown)
    expect(like.lacking.size).toBe(0)
    expect(like.assumed.find((entry) => entry.input === input)).toMatchObject({ kind: 'requiredInput' })
    expect(like.assumed.find((entry) => entry.input === input)?.cells).toContain(cell)
  })

  it('Blatt 15: hochwertige Einheiten, Zufallsschicht und Auswahlintervall', () => {
    const results = run(sheet15)
    expect(results).toMatchObject({ C16: 3700000, C17: 21, C18: '✔ ≥ 3 Einheiten', C21: '✔ keine weitere Iteration', C24: 2400 })
    expect(results.C19).toBeCloseTo(176190.48, 2)
    expect(run(sheet15, { C10: 5 })).toMatchObject({ C17: 2, C18: '✖ < 3 Einheiten (Art. 5 Abs. 5)' })
    expect(run(sheet15, { C10: 3 })).toMatchObject({ C17: 0, C19: null, C26: null })
    expect(run(sheet15, { C10: null })).toMatchObject({ C17: null, C18: null, C19: null, C30: null, N10: null })
  })

  it('Summen aus Blatt 17 haben ein Ziel', () => {
    const roles = (sheet: AvailableSheet): Record<string, string> => Object.fromEntries(fieldsOf(sheet.definition).filter((field) => field.subsample).map((field) => [field.cell, field.subsample!]))
    expect(roles(sheet13)).toEqual({ C17: 'bookValueSum', C18: 'errorSum', C19: 'highValueErrors' })
    expect(roles(sheet15)).toEqual({ C22: 'highValueErrors', C23: 'errorRateSum' })
  })
})

describe.each([
  { sheet: sheet14, key: 11, rows: [11, 12, 24, 25], errors: 25, projected: 27, total: 'C29', size: 'C16', affected: ['C27', 'C29', 'C32', 'C33', 'C35'] },
  { sheet: sheet16, key: 9, rows: [9, 10, 19, 20, 25, 26], errors: 26, projected: 28, total: 'C30', size: 'C13', affected: ['C28', 'C30', 'C33', 'C34', 'C36'] },
])('Geschichtete Blätter: $sheet.id', ({ sheet, key, rows, errors, projected, total, size, affected }) => {
  /** Beispielwerte, in denen die Schicht aus Spalte `from` in Spalte `to` steht. */
  const moved = (from: string, to: string): Record<string, CellValue> => {
    const inputs: Record<string, CellValue> = { ...sheet.sample.inputs }
    for (const row of rows) {
      inputs[`${to}${row}`] = inputs[`${from}${row}`] ?? null
      delete inputs[`${from}${row}`]
    }
    return inputs
  }

  it('Spalte AA rechnet wie Spalte D', () => {
    const base = run(sheet)
    const other = sheet.compute(moved('D', 'AA'), context)
    for (const field of fieldsOf(sheet.definition)) {
      if (!field.columns) expect(other[field.cell], field.cell).toBe(base[field.cell])
      else {
        expect(other[`AA${field.cell.slice(1)}`], field.cell).toBe(base[field.cell])
        if (field.total) expect(other[field.total], field.total).toBeCloseTo(base[field.total] as number, 6)
      }
    }
    for (const cell of Object.values(SUMMARY_CELLS)) expect(other[cell], cell).toBe(base[cell])
    expect(hintIds(sheet, moved('D', 'AA'))).toContain('strata-beyond-template')
    expect(hintIds(sheet, { ...sheet.sample.inputs })).not.toContain('strata-beyond-template')
  })

  it('jede Schichtzeile hat 20 Zellen; leere Schichten bleiben ohne Wert bzw. liefern 0', () => {
    const results = run(sheet)
    for (const column of [...TEMPLATE_STRATA.slice(3), ...EXTRA_STRATA]) {
      expect(results[`${column}${projected}`]).toBe(0)
      expect(results[`${column}${projected === 27 ? 18 : 15}`]).toBeNull()
    }
  })

  it('ohne Stichprobenumfang bleiben Schichtumfänge, Summen und Folgegrößen offen', () => {
    const results = run(sheet, { [size]: null })
    const allocation = projected === 27 ? 18 : 15
    expect([results[`D${allocation}`], results[`C${allocation}`], results.N10, named(sheet.definition, results).checkCoverage]).toEqual([null, null, null, null])
  })

  it('fehlt die Fehlersumme einer Schicht, rechnet sie wie in der Vorlage mit 0 und wird ausgewiesen', () => {
    const results = run(sheet, { [`E${errors}`]: null })
    expect(results[total]).toBeGreaterThan(0)
    expect(sheet.zeroAssumed?.(results)).toEqual([{ input: `E${errors}`, cells: [`E${projected}`, ...affected, 'N5', 'N11'], kind: 'partialErrorSum' }])
    const all = run(sheet, { [`D${errors}`]: null, [`E${errors}`]: null, [`F${errors}`]: null })
    expect(all[total]).toBeNull()
    expect(sheet.zeroAssumed?.(all)).toEqual([])
    expect(buildSummary(sheet, { ...sheet.sample.inputs, [`E${errors}`]: null }, results, context, t).hints.map((hint) => hint.id)).toContain(`zero-E${errors}`)
  })

  it('Fallart partialErrorSum: geltend mit 0 gerechnet und ausgewiesen, streng offen mit Nennung der Eingabe', () => {
    const current = evaluate(sheet, { [`E${errors}`]: null })
    expect(current.cells[`E${projected}`]).toBe(sheet === sheet14 ? 0 : (current.cells.E25 as number))
    expect(current.cells[total]).toBeGreaterThan(0)
    expect(current.cells.N11).toBeGreaterThan(0)
    expect(current.assumed).toEqual([{ input: `E${errors}`, cells: [`E${projected}`, ...affected, 'N5', 'N11'], kind: 'partialErrorSum' }])
    expect(current.lacking.size).toBe(0)
    expect(evaluate(sheet, { [`E${errors}`]: null }, template).cells).toEqual(current.cells)
    const open = evaluate(sheet, { [`E${errors}`]: null }, strict)
    expect([`E${projected}`, ...affected, 'N5', 'N11'].map((cell) => open.cells[cell])).toEqual(Array.from({ length: affected.length + 3 }, () => null))
    expect(open.assumed).toEqual([])
    expect(open.lacking.get(total)).toEqual([`E${errors}`])
    expect(open.lacking.get('N11')).toEqual([`E${errors}`])
  })

  it('Fallart requiredInput: ohne Stichprobenumfang „Angabe fehlt“ mit Nennung der Eingabe; wie die Vorlage je Schicht 1', () => {
    const allocation = projected === 27 ? 18 : 15
    const current = evaluate(sheet, { [size]: null })
    expect([current.cells[`D${allocation}`], current.cells[`C${allocation}`], current.cells.N10]).toEqual([null, null, null])
    expect(current.lacking.get(`C${allocation}`)).toEqual([size])
    expect(current.lacking.get('N10')).toEqual([size])
    const like = evaluate(sheet, { [size]: null }, template)
    expect([like.cells[`D${allocation}`], like.cells[`C${allocation}`]]).toEqual([1, 3])
    expect(like.lacking.size).toBe(0)
    expect(like.assumed.find((entry) => entry.input === size)).toMatchObject({ kind: 'requiredInput' })
  })

  it('Hinweise der Webfassung zu den Schichten nennen die Schichtnummer und verändern kein Ergebnis', () => {
    const ignored = { ...sheet.sample.inputs, [`E${key}`]: null }
    expect(hintIds(sheet, ignored)).toContain('stratum-ignored-2')
    expect(sheet.webHints?.(ignored, sheet.compute(ignored, context), context).find((hint) => hint.id === 'stratum-ignored-2')?.text).toMatch(/^Schicht 2: /)
    expect(sheet.compute(ignored, context)[`E${projected}`]).toBe(0)
    const beyond = { ...moved('F', 'AB'), [`AB${key}`]: null, [`E${key}`]: null }
    expect(hintIds(sheet, beyond).filter((id) => id.startsWith('stratum-ignored'))).toEqual(['stratum-ignored-2', 'stratum-ignored-9'])
    expect(buildSummary(localizeSheet(sheet, 'en'), beyond, sheet.compute(beyond, context), context, t).hints.filter((hint) => hint.id.startsWith('stratum-ignored')).map((hint) => hint.text.slice(0, 11))).toEqual(['Stratum 2: ', 'Stratum 9: '])
    expect(hintIds(sheet, { ...sheet.sample.inputs, [size]: 400 })).toContain('size-exceeds-population')
  })
})

/** Werte der Vorlage ohne Grundlage, negative Ergebnisse und ihre Hinweise: `sheets13to16.limits.spec.ts`. */
describe('Blatt 14 und 16: einzelne Schichten', () => {
  it('Blatt 14: fehlt der Buchwert einer belegten Schicht, bleiben Summe und Fehlerquote offen', () => {
    const results = run(sheet14, { E12: null })
    expect([results.E27, results.C27, results.C29, results.C33, results.C35]).toEqual([null, null, null, null, null])
    expect(results.D27).toBeGreaterThan(0)
  })

  it('Blatt 14: fehlt die Summe der Buchwerte der Stichprobe einer Schicht, summiert die Webfassung wie die Vorlage ohne sie', () => {
    const results = run(sheet14, { E24: null })
    expect(results.E27).toBeNull()
    expect(results.C27).toBeCloseTo((results.D27 as number) + (results.F27 as number), 6)
    expect(hintIds(sheet14, { ...sheet14.sample.inputs, E24: null })).toContain('stratum-not-projected-2')
  })

  it('Blatt 14: Aufrundung je Schicht hebt die Summe über den Umfang', () => {
    const results = run(sheet14)
    expect([results.D18, results.E18, results.F18, results.C18, results.C19]).toEqual([10, 8, 5, 23, 27])
    expect(hintIds(sheet14, { ...sheet14.sample.inputs })).toEqual(['strata-sum-exceeds-size'])
  })

  it('Blatt 16: alle Einheiten einer Schicht hochwertig – kein Auswahlintervall, Schicht nicht in der Summe', () => {
    const inputs = { ...sheet16.sample.inputs, F19: 5, F20: 830000 }
    const results = sheet16.compute(inputs, context)
    expect([results.F22, results.F23, results.F28]).toEqual([0, null, null])
    expect(results.C28).toBeCloseTo((results.D28 as number) + (results.E28 as number), 6)
    expect(hintIds(sheet16, inputs)).toContain('stratum-not-projected-3')
  })

  it('Blatt 16, Rechenkern ohne Anzahl der Einheiten: N und seine Summe sind ohne Grundlage (offen, solange eine Eingabe fehlt), der Buchwert nicht', () => {
    const results = run(sheet16, { D10: null, E10: null, F10: null })
    expect([results.C10, results.C11, results.C12, results.C16, results.C17]).toEqual([null, null, null, null, null])
    expect(results.C34).toBeGreaterThan(0)
  })
})
