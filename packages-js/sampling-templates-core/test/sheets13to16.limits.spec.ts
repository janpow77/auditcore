/**
 * Blätter 13–16: Werte der Vorlage ohne Grundlage und negative Ergebnisse.
 * Verbindliche Regel: Sind alle Pflichteingaben vorhanden, zeigt die Webfassung,
 * was die Vorlage zeigt – mit Hinweis in Warnfarbe und einer nicht
 * uneingeschränkt grünen Würdigung. Offen bleibt ein Wert ohne Grundlage nur,
 * solange eine Pflichteingabe fehlt.
 */
import { describe, expect, it } from 'vitest'
import { createTranslate } from '../src/i18n/messages'
import { fieldsOf, named } from '../src/model/definition'
import { evaluateSheet, type SheetEvaluation } from '../src/model/evaluate'
import { createContext, type AvailableSheet } from '../src/model/sheet'
import { STRATA_COLUMNS, TEMPLATE_STRATA } from '../src/model/strata'
import type { CellValue } from '../src/model/types'
import { sheet as sheet14 } from '../src/sheets/14_NS_GW_S/index'
import { sheet as sheet15 } from '../src/sheets/15_NS_PPS/index'
import { sheet as sheet16 } from '../src/sheets/16_NS_PPS_S/index'
import { isQualified, limitationsOf, type Limitation } from '../src/view/limits'
import { buildHints, type HintView } from '../src/view/summaryView'

type Inputs = Record<string, CellValue>

const context = createContext()
const t = createTranslate()
const PASSED = '✔ Gesamtfehlerquote unter der Signifikanzschwelle'

interface Shown {
  evaluation: SheetEvaluation
  cells: SheetEvaluation['cells']
  limitations: Limitation[]
  hints: HintView[]
}

/** Was die Webfassung zu den Eingaben zeigt: Zellwerte, Einschränkungen und Hinweise der Ergebnisspalte. */
function show(sheet: AvailableSheet, inputs: Inputs): Shown {
  const evaluation = evaluateSheet(sheet, inputs, context)
  return { evaluation, cells: evaluation.cells, limitations: limitationsOf(sheet, inputs, evaluation.cells, context, t), hints: buildHints(sheet, inputs, evaluation.cells, context, t) }
}

const sample = (sheet: AvailableSheet, changes: Inputs = {}): Inputs => ({ ...sheet.sample.inputs, ...changes })
/** Summen freiwilliger Schichtzeilen in Blatt 16 (hochwertige Einheiten): wie in der Vorlage 0, kein Wert ohne Grundlage (Entscheidung des Inhabers vom 17.10.2026). */
const OPTIONAL16 = ['C19', 'C20', 'C25', 'C29', 'N6']
const required16 = (cells: readonly string[]): string[] => cells.filter((cell) => !OPTIONAL16.includes(cell))
const values = (shown: Shown, cells: readonly string[]): CellValue[] => cells.map((cell) => shown.cells[cell] ?? null)
const open = (cells: readonly string[]): null[] => cells.map(() => null)
const ids = (shown: Shown): string[] => shown.limitations.map((entry) => entry.id)

/** Wie die Vorlage gezeigt und ausgewiesen: Hinweis `without-basis` in Warnfarbe, Würdigung nicht uneingeschränkt grün. */
function expectWithoutBasis(shown: Shown, cells: readonly string[], assessment?: string): void {
  expect(shown.evaluation.complete).toBe(true)
  expect(shown.evaluation.withoutBasis).toEqual(expect.arrayContaining([...cells]))
  expect(shown.limitations.find((entry) => entry.kind === 'withoutBasis')).toMatchObject({ id: 'without-basis', tone: 'warning' })
  expect(isQualified(shown.limitations)).toBe(true)
  expect(shown.hints.find((hint) => hint.id === 'without-basis')).toMatchObject({ tone: 'warning', source: 'web' })
  if (assessment) expect(shown.hints.find((hint) => hint.id === assessment)).toMatchObject({ tone: 'warning' })
}

/** Eine Pflichteingabe fehlt: Werte ohne Grundlage bleiben offen, nichts wird als „wie die Vorlage“ ausgewiesen. */
function expectOpen(shown: Shown, cells: readonly string[]): void {
  expect(shown.evaluation.complete).toBe(false)
  expect(values(shown, cells)).toEqual(open(cells))
  expect(shown.evaluation.withoutBasis).toEqual([])
  expect(ids(shown)).not.toContain('without-basis')
}

describe('Summen ohne Summanden: keine Schicht belegt', () => {
  const emptied = (sheet: AvailableSheet, rows: readonly number[]): Inputs => sample(sheet, Object.fromEntries(rows.flatMap((row) => STRATA_COLUMNS.map((column) => [`${column}${row}`, null]))))
  const totalsOf = (sheet: AvailableSheet): string[] => fieldsOf(sheet.definition).flatMap((field) => (field.total ? [field.total] : []))

  it('Blatt 16, Pflichteingaben vollständig: Summen 0 und „✔“ wie in der Vorlage, ausgewiesen als Werte ohne Grundlage', () => {
    const totals = totalsOf(sheet16)
    const shown = show(sheet16, emptied(sheet16, [9, 10, 19, 20, 25, 26]))
    expect(values(shown, totals)).toEqual(totals.map(() => 0))
    const result = named(sheet16.definition, shown.cells)
    expect([result.populationSize, result.checkAdmissibility, result.minimumCoverage, shown.cells.N4, shown.cells.N10]).toEqual([0, '✔ N < 300: zulässig (Art. 79 Abs. 2 VO (EU) 2021/1060; Art. 6 Abs. 1)', 0, 0, 0])
    expect(String(result.checkCoverage)).toMatch(/^✔ /)
    // Ohne Summe der Fehlerquoten zeigt auch die Vorlage keinen extrapolierten Fehler und keine Würdigung.
    expect(values(shown, ['C30', 'C34', 'C36', 'N5', 'N11'])).toEqual([null, null, null, null, null])
    expect([...shown.evaluation.lacking.keys()]).toEqual([])
    expectWithoutBasis(shown, required16([...totals, 'C11', 'C12', 'C16', 'C17', 'N4', 'N10']))
  })

  it('Blatt 16, Stichprobenumfang fehlt: dieselben Summen und Folgezellen bleiben offen', () => {
    const shown = show(sheet16, { ...emptied(sheet16, [9, 10, 19, 20, 25, 26]), C13: null })
    expectOpen(shown, required16([...totalsOf(sheet16), 'C11', 'C12', 'C16', 'C17', 'N4', 'N10']))
    expect(values(shown, ['C19', 'C20', 'C25'])).toEqual([0, 0, 0])
  })

  it('Blatt 14: ohne belegte Schicht fehlt der Buchwert der ersten Schicht (Pflichteingabe) – Summen und Folgezellen bleiben offen', () => {
    const shown = show(sheet14, emptied(sheet14, [11, 12, 24, 25]))
    const result = named(sheet14.definition, shown.cells)
    expectOpen(shown, [...totalsOf(sheet14), 'N4', 'N5', 'N10', 'N11'])
    expect([result.populationSize, result.checkAdmissibility, result.minimumCoverage, result.checkCoverage]).toEqual([null, null, null, null])
  })
})

describe('Blatt 14 und 16: keine belegte Schicht ist hochrechenbar', () => {
  const affected14 = ['C27', 'C29', 'C33', 'C35', 'N5', 'N11']
  const affected16 = ['C28', 'C30', 'C34', 'C36', 'N5', 'N11']
  /** Eine Schicht, deren Einheiten alle hochwertig sind: kein Auswahlintervall, kein extrapolierter Fehler der Schicht. */
  const allHighValue: Inputs = { C13: 22, C35: 0.02, D9: 4230000, D10: 180, D19: 22, D20: 4230000, D25: 2400, D26: 0.05 }

  it('Blatt 14, vollständig: Summe 0 €, EE, Fehlerquote und „✔“ wie in der Vorlage – mit Hinweis, Würdigung nicht grün', () => {
    const shown = show(sheet14, sample(sheet14, { D24: null, E24: null, F24: null }))
    expect(values(shown, ['D27', ...affected14])).toEqual([null, 0, 1200, 1200 / 4850000, PASSED, 1200, 1200 / 4850000])
    expectWithoutBasis(shown, affected14, 'C35')
    // Die fehlenden Summen der Buchwerte der Stichprobe sind stille Lücken; je Schicht steht der Hinweis der Webfassung.
    expect(shown.evaluation.silent).toEqual(['D24', 'E24', 'F24'])
    expect(ids(shown)).toEqual(expect.arrayContaining(['missing-D24', 'stratum-not-projected-1', 'stratum-not-projected-2', 'stratum-not-projected-3']))
    expect(shown.hints.filter((hint) => hint.tone === 'success').map((hint) => hint.id)).not.toContain('C35')
  })

  it('Blatt 14, Umfang der Zufallsstichprobe fehlt: Summe, EE, Fehlerquote und Würdigung bleiben offen', () => {
    expectOpen(show(sheet14, sample(sheet14, { D24: null, E24: null, F24: null, C16: null })), ['D27', ...affected14])
  })

  it('Blatt 16, vollständig: Summe, EE und Fehlerquote 0 und „✔“ wie in der Vorlage – mit Hinweis, Würdigung nicht grün', () => {
    const shown = show(sheet16, allHighValue)
    expect(values(shown, ['D22', 'D28', 'C29', ...affected16])).toEqual([0, null, 2400, 0, 0, 0, PASSED, 0, 0])
    expectWithoutBasis(shown, affected16, 'C36')
    expect(ids(shown)).toContain('stratum-not-projected-1')
  })

  it('Blatt 16, Stichprobenumfang fehlt: Summe, EE, Fehlerquote und Würdigung bleiben offen', () => {
    const shown = show(sheet16, { ...allHighValue, C13: null })
    expectOpen(shown, ['D22', 'D28', ...affected16])
    expect(shown.cells.C29).toBe(2400)
    expect(shown.evaluation.lacking.get('C30')).toEqual(['C13'])
  })
})

describe('Blatt 16: keine Schicht trägt Fehler hochwertiger Einheiten', () => {
  const changes: Inputs = { D25: null, E25: null, F25: null }

  it('vollständig: Summe, EE_e und N6 zeigen 0 wie die Vorlage – freiwillig, kein Wert ohne Grundlage; EE ist davon unberührt', () => {
    const shown = show(sheet16, sample(sheet16, changes))
    expect(values(shown, ['C25', 'C29', 'N6'])).toEqual([0, 0, 0])
    expect(shown.cells.C30).toBeGreaterThan(0)
    expect(shown.evaluation.withoutBasis).not.toEqual(expect.arrayContaining(['C25']))
    // Hochwertige Einheiten sind eingetragen, ihre Fehler nicht: stille Lücke je Schicht.
    expect(ids(shown)).toEqual(expect.arrayContaining(['missing-D25', 'missing-E25', 'missing-F25']))
  })

  it('Stichprobenumfang fehlt: Summe, EE_e und N6 zeigen 0, die Hochrechnung bleibt offen', () => {
    const shown = show(sheet16, sample(sheet16, { ...changes, C13: null }))
    expect(values(shown, ['C25', 'C29', 'N6'])).toEqual([0, 0, 0])
    expectOpen(shown, ['C30'])
  })
})

describe('Mehr hochwertige Einheiten als Stichprobenumfang (Abnahme, Auflage V3)', () => {
  const NEGATIVE = ['negative-random-stratum', 'negative-result']

  /** Werte wie gerechnet, beide Hinweise in Warnfarbe, Würdigung „✔“ nicht in Ton `success`. */
  function expectNegative(sheet: AvailableSheet, inputs: Inputs, shown: Shown, assessment: string): void {
    expect(shown.cells).toEqual(sheet.compute(inputs, context))
    expect([shown.evaluation.complete, shown.evaluation.withoutBasis, [...shown.evaluation.lacking.keys()]]).toEqual([true, [], []])
    for (const id of NEGATIVE) expect(shown.limitations.find((entry) => entry.id === id), id).toMatchObject({ kind: 'negative', tone: 'warning' })
    expect(isQualified(shown.limitations)).toBe(true)
    expect(shown.cells[assessment]).toBe(PASSED)
    expect(shown.hints.find((hint) => hint.id === assessment)?.tone).toBe('warning')
    expect(shown.hints.filter((hint) => hint.tone === 'success').map((hint) => hint.id)).not.toContain(assessment)
    for (const id of NEGATIVE) expect(shown.hints.find((hint) => hint.id === id), id).toMatchObject({ tone: 'warning', source: 'web' })
  }

  it('Blatt 15 mit C10 = 8 und C14 = 79: negative Zufallsschicht und negative Gesamtfehlerquote bleiben wie gerechnet', () => {
    const inputs = sample(sheet15, { C10: 8, C14: 79 })
    const shown = show(sheet15, inputs)
    expect(values(shown, ['C17', 'C18', 'N10'])).toEqual([-71, '✖ < 3 Einheiten (Art. 5 Abs. 5)', 8])
    expect(shown.cells.C19).toBeCloseTo(3700000 / -71, 6)
    expect(shown.cells.C26).toBeCloseTo(2400 + (3700000 / -71) * 0.085, 6)
    expect(shown.cells.C30).toBeCloseTo((2400 + (3700000 / -71) * 0.085) / 4850000, 12)
    expect(shown.cells.C30).toBeLessThan(0)
    expectNegative(sheet15, inputs, shown, 'C32')
    expect(shown.limitations.find((entry) => entry.id === 'negative-result')?.text).toMatch(/Zufallsschicht.*Auswahlintervall.*Gesamtfehlerquote/)
  })

  it('Blatt 16 mit sieben Schichten, C13 = 50 und D19–J19 = 371 … 184: negative Zufallsschichten bleiben wie gerechnet', () => {
    const rows: Readonly<Record<number, readonly number[]>> = {
      9: [1900000, 1500000, 830000, 1200000, 2100000, 640000, 980000],
      10: [80, 60, 36, 25, 40, 20, 30],
      19: [371, 196, 100, 164, 443, 76, 184],
      20: [520000, 260000, 90000, 150000, 400000, 70000, 170000],
      25: [1800, 0, 0, 0, 0, 0, 0],
      26: [0.062, 0.048, 0.021, 0.03, 0.04, 0.01, 0.02],
    }
    const strata = Object.fromEntries(Object.entries(rows).flatMap(([row, cells]) => TEMPLATE_STRATA.map((column, index) => [`${column}${row}`, cells[index]!])))
    const inputs = sample(sheet16, { C13: 50, ...strata })
    const shown = show(sheet16, inputs)
    expect(values(shown, TEMPLATE_STRATA.map((column) => `${column}15`))).toEqual([11, 9, 5, 7, 12, 4, 6])
    expect(values(shown, [...TEMPLATE_STRATA.map((column) => `${column}22`), 'C22'])).toEqual([-360, -187, -95, -157, -431, -72, -178, -1480])
    expect(shown.cells.D23).toBeCloseTo(1380000 / -360, 6)
    expect(shown.cells.E28).toBeLessThan(0)
    expect(shown.cells.C34).toBeCloseTo((shown.cells.C30 as number) / 9150000, 12)
    expectNegative(sheet16, inputs, shown, 'C36')
    expect(shown.limitations.find((entry) => entry.id === 'negative-result')?.text).toMatch(/\(Schicht 1, 2, 3, 4, 5, 6, 7\)/)
  })
})
