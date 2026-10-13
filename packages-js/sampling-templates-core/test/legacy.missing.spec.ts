/**
 * Altvorlagen von 2017 (Blätter X1–X4): fehlende Angaben nach der Richtlinie
 * (`src/model/policy.ts`). Geprüft wird über `evaluateSheet`, was die
 * Webfassung zeigt – beim leeren und beim teilweise ausgefüllten Formular und
 * je Fallart: Pflichteingabe fehlt (`requiredInput`), Standardabweichung der
 * Stichprobe fehlt (`sampleDeviation`), Fehlersumme einer Schicht bzw. eines
 * Zeitraums fehlt neben einer eingetragenen (`partialErrorSum`), Wert der
 * Vorlage ohne Grundlage (`withoutBasis`).
 */
import { describe, expect, it } from 'vitest'
import { createTranslate } from '../src/i18n/messages'
import { evaluateSheet, type SheetEvaluation } from '../src/model/evaluate'
import { STRICT_POLICY, TEMPLATE_POLICY } from '../src/model/policy'
import { createContext, localizeSheet, type AvailableSheet } from '../src/model/sheet'
import type { CellValue, MissingPolicy } from '../src/model/types'
import { sheet as x1 } from '../src/sheets/X1_KonsMUS_2017/index'
import { sheet as x2 } from '../src/sheets/X2_DiffSch_2017/index'
import { sheet as x3 } from '../src/sheets/X3_DiffSch_S_2017/index'
import { sheet as x4 } from '../src/sheets/X4_DiffSch_2Z_2017/index'
import { LEGACY_NOTICE, LEGACY_STRATA } from '../src/sheets/shared/legacy'
import { buildSummary } from '../src/view/summaryView'

type Inputs = Record<string, CellValue>

/** Auswertung der Beispielwerte mit Änderungen (`null` leert eine Eingabe). */
function evaluate(sheet: AvailableSheet, changes: Inputs = {}, policy?: MissingPolicy): SheetEvaluation {
  return evaluateSheet(sheet, { ...sheet.sample.inputs, ...changes }, createContext(policy ? { policy } : {}))
}

/** Zellen mit einem Wert, ohne die Eingaben. */
function shown(sheet: AvailableSheet, inputs: Inputs): Inputs {
  const cells = evaluateSheet(sheet, inputs, createContext()).cells
  return Object.fromEntries(Object.entries(cells).filter(([cell, value]) => value !== null && !(cell in inputs)))
}

/**
 * Was das leere Formular zeigen darf: den Hinweis der Altvorlage und die
 * Wesentlichkeitsschwelle, die in den Altvorlagen ein fester Wert ist (2 %).
 */
const EMPTY_FORM: readonly { sheet: AvailableSheet; allowed: Inputs }[] = [
  { sheet: x1, allowed: { G1: LEGACY_NOTICE, C9: 0.02 } },
  { sheet: x2, allowed: { E1: LEGACY_NOTICE, C9: 0.02 } },
  { sheet: x3, allowed: { M1: LEGACY_NOTICE, D13: 0.02 } },
  { sheet: x4, allowed: { F1: LEGACY_NOTICE, C14: 0.02, C29: 0.02 } },
]

describe.each(EMPTY_FORM)('Leeres Formular $sheet.id', ({ sheet, allowed }) => {
  it('zeigt nur den Hinweis der Altvorlage und die feste Wesentlichkeitsschwelle', () => {
    expect(shown(sheet, {})).toEqual(allowed)
    expect(evaluateSheet(sheet, {}, createContext()).assumed).toEqual([])
    expect(sheet.webHints?.({}, sheet.compute({}, createContext()), createContext()) ?? []).toEqual([])
  })

  it('zeigt auch mit einer einzelnen Eingabe keinen Stichprobenumfang und kein Ergebnis', () => {
    const level = sheet === x1 ? 'C4' : sheet === x2 ? 'C5' : sheet === x3 ? 'D9' : 'C10'
    const factor = sheet === x1 ? { C5: 2.31, C6: 1.5 } : sheet === x2 ? { C6: 1.645 } : sheet === x3 ? { D10: 1.645 } : { C11: 1.645 }
    expect(shown(sheet, { [level]: 0.9 })).toEqual({ ...allowed, ...factor })
  })
})

describe('Teilweise ausgefülltes Formular', () => {
  it('X3 ohne Schicht: Summen, Fehlerbeträge und Hochrechnung bleiben offen, die Summen nennen die fehlenden Angaben', () => {
    const inputs = { D9: 0.9, D11: 0.005 }
    expect(shown(x3, inputs)).toEqual({ M1: LEGACY_NOTICE, D13: 0.02, D10: 1.645 })
    const lacking = evaluateSheet(x3, inputs, createContext()).lacking
    // Ist keine Schicht belegt, nennt die Anzeige die Zellen der ersten Schicht, nicht alle zwanzig.
    expect(lacking.get('D1')).toEqual(['E6'])
    expect(lacking.get('D3')).toEqual(['E7'])
    // Die Hochrechnung ist auch in der Vorlage nur eine Summe ohne Summanden: keine Angabe fehlt, es gibt nichts zu zeigen.
    for (const cell of ['D23', 'D24', 'D25']) expect(lacking.has(cell), cell).toBe(false)
  })

  it('X3 nur Planung: Umfang und Schichtumfänge stehen, die Hochrechnung bleibt offen', () => {
    const planning = evaluate(x3, { E19: null, F19: null, G19: null, E21: null, F21: null, G21: null })
    expect([planning.cells.D15, planning.cells.E17, planning.cells.F17, planning.cells.G17]).toEqual([83, 42, 30, 12])
    for (const cell of ['E20', 'E22', 'D23', 'D24', 'D25', 'D28', 'D29']) expect(planning.cells[cell], cell).toBeNull()
    expect(planning.lacking.get('D23')).toEqual(expect.arrayContaining(['E19', 'F19', 'G19']))
    expect(planning.assumed.map((entry) => entry.input)).toEqual(['E21', 'F21', 'G21'])
  })

  it('X4 nur erster Zeitraum: Planung steht, Neuberechnung und Ergebnisse entstehen nicht aus dem ersten Zeitraum allein', () => {
    const first = evaluate(x4, { C23: null, C25: null, C26: null, C27: null, C33: null, C34: null, C35: null })
    expect([first.cells.C16, first.cells.C17, first.cells.C18]).toEqual([77, 43, 34])
    for (const cell of ['C24', 'C28', 'C30', 'C31', 'C36', 'C37', 'C38', 'C39', 'C40', 'C41', 'C42', 'C43']) expect(first.cells[cell], cell).toBeNull()
    expect(first.lacking.get('C31')).toEqual(expect.arrayContaining(['C23', 'C25', 'C26', 'C27']))
    expect(first.assumed).toEqual([])
  })
})

describe('Pflichteingabe fehlt (requiredInput)', () => {
  it('X1 ohne erwartete Fehlerquote: Umfang und Folgegrößen offen, die Eingabe wird genannt', () => {
    const current = evaluate(x1, { C7: null })
    for (const cell of ['C8', 'C11', 'C12', 'C15', 'C19', 'C22']) expect(current.cells[cell], cell).toBeNull()
    expect(current.lacking.get('C11')).toEqual(['C7'])
    expect(current.assumed).toEqual([])
    const template = evaluate(x1, { C7: null }, TEMPLATE_POLICY)
    expect(template.cells.C11).toBe(116)
    expect(template.lacking.size).toBe(0)
    expect(template.assumed.find((entry) => entry.input === 'C7')).toMatchObject({ kind: 'requiredInput' })
  })

  it('X2 ohne Fehler der Stichprobe: Hochrechnung offen, der Umfang steht', () => {
    const current = evaluate(x2, { C13: null })
    expect(current.cells.C11).toBeGreaterThanOrEqual(30)
    for (const cell of ['C14', 'C16', 'C17', 'C18', 'C21', 'C22']) expect(current.cells[cell], cell).toBeNull()
    expect(current.lacking.get('C16')).toEqual(['C13'])
  })

  it('X4 ohne Standardabweichung der Stichprobe des ersten Zeitraums: Sie geht in die Neuberechnung ein, der Umfang bleibt offen', () => {
    const current = evaluate(x4, { C22: null })
    for (const cell of ['C31', 'C36', 'C37', 'C38', 'C39', 'C40', 'C41', 'C42']) expect(current.cells[cell], cell).toBeNull()
    expect(current.lacking.get('C31')).toEqual(['C22'])
    expect(current.assumed).toEqual([])
    const template = evaluate(x4, { C22: null }, TEMPLATE_POLICY)
    expect(template.cells.C31).toBe(24)
    expect(template.assumed).toEqual([{ input: 'C22', cells: ['C31', 'C39', 'C40', 'C36', 'C37', 'C38', 'C41', 'C42'], kind: 'requiredInput' }])
  })

  it('X3: eine Angabe der achten Schicht (Spalte AA) fehlt – „Angabe fehlt“ gilt auch jenseits der sieben Spalten der Vorlage', () => {
    const current = evaluate(x3, { AA6: 2000000, AA7: 40, AA19: 900 })
    expect([current.cells.D1, current.cells.D3]).toEqual([50500000, 460])
    for (const cell of ['D4', 'D15', 'E17', 'AA17', 'AA20', 'AA22', 'D23', 'D26']) expect(current.cells[cell], cell).toBeNull()
    expect(current.lacking.get('D15')).toContain('AA8')
    expect(current.lacking.get('AA17')).toContain('AA8')
  })
})

describe('Standardabweichung der Stichprobe fehlt (sampleDeviation)', () => {
  it('X2 ohne C15: Genauigkeit 0, ausgewiesen; streng offen mit Nennung der Eingabe', () => {
    const current = evaluate(x2, { C15: null })
    expect(current.cells.C19).toBe(0)
    expect(current.cells.C21).toBe(current.cells.C17)
    expect(current.assumed).toEqual([{ input: 'C15', cells: ['C19', 'C20', 'C21', 'C22'] }])
    expect(current.lacking.size).toBe(0)
    const strict = evaluate(x2, { C15: null }, STRICT_POLICY)
    for (const cell of ['C19', 'C20', 'C21', 'C22']) expect(strict.cells[cell], cell).toBeNull()
    expect(strict.cells.C16).toBe(current.cells.C16)
    expect(strict.lacking.get('C19')).toEqual(['C15'])
    expect(strict.assumed).toEqual([])
    const inputs = { ...x2.sample.inputs, C15: null }
    expect(buildSummary(x2, inputs, x2.compute(inputs, createContext()), createContext(), createTranslate()).hints.map((hint) => hint.id)).toContain('zero-C15')
    expect(x2.zeroAssumed?.(x2.compute({ C1: 1000000 }, createContext()))).toEqual([])
  })

  it('X3 ohne s einer belegten Schicht: ihr Beitrag zur Genauigkeit zählt 0, ausgewiesen', () => {
    const current = evaluate(x3, { F21: null })
    const full = evaluate(x3)
    expect(current.cells.D26).toBeLessThan(full.cells.D26 as number)
    expect(current.cells.D23).toBe(full.cells.D23)
    expect(current.assumed).toEqual([{ input: 'F21', cells: ['D26', 'D27', 'D28', 'D29'] }])
    expect(evaluate(x3, { D9: null, F21: null }).assumed).toEqual([])
    const strict = evaluate(x3, { F21: null }, STRICT_POLICY)
    expect([strict.cells.D26, strict.cells.D28, strict.cells.D23]).toEqual([null, null, full.cells.D23])
    expect(strict.lacking.get('D26')).toEqual(['F21'])
  })

  it('X4 ohne C35: Genauigkeit ohne den Beitrag des zweiten Zeitraums, ausgewiesen; Umfang und Hochrechnung unberührt', () => {
    const current = evaluate(x4, { C35: null })
    const full = evaluate(x4)
    expect([current.cells.C31, current.cells.C36]).toEqual([full.cells.C31, full.cells.C36])
    expect(current.cells.C39).toBeLessThan(full.cells.C39 as number)
    expect(current.assumed).toEqual([{ input: 'C35', cells: ['C39', 'C40', 'C41', 'C42'] }])
    expect(evaluate(x4, { C35: null }, STRICT_POLICY).lacking.get('C39')).toEqual(['C35'])
  })
})

describe('Fehlersumme einer Schicht bzw. eines Zeitraums fehlt (partialErrorSum)', () => {
  it('X3: Fehler einer Schicht leer, andere Schichten tragen einen – wie die Vorlage mit 0 gerechnet und ausgewiesen', () => {
    const current = evaluate(x3, { F19: null })
    expect([current.cells.F20, current.cells.F22, current.cells.D23]).toEqual([0, 0, 95000])
    expect(current.assumed).toEqual([{ input: 'F19', cells: ['F20', 'F22', 'D23', 'D24', 'D25', 'D28', 'D29'], kind: 'partialErrorSum' }])
    expect(current.lacking.size).toBe(0)
    const strict = evaluate(x3, { F19: null }, STRICT_POLICY)
    for (const cell of ['F20', 'F22', 'D23', 'D24', 'D25', 'D28', 'D29']) expect(strict.cells[cell], cell).toBeNull()
    expect(strict.cells.D26).toBe(current.cells.D26)
    expect(strict.lacking.get('D23')).toEqual(['F19'])
  })

  it('X3: Fehler und s derselben Schicht leer – beides ausgewiesen; achte Schicht (AA) wie jede andere', () => {
    expect(evaluate(x3, { F19: null, F21: null }).assumed.map((entry) => [entry.input, entry.kind])).toEqual([['F19', 'partialErrorSum'], ['F21', undefined]])
    const eighth = evaluate(x3, { AA6: 2000000, AA7: 40, AA8: 6000, AA21: 1500 })
    expect(eighth.assumed).toEqual([{ input: 'AA19', cells: ['AA20', 'AA22', 'D23', 'D24', 'D25', 'D28', 'D29'], kind: 'partialErrorSum' }])
    expect([eighth.cells.AA20, eighth.cells.AA22]).toEqual([0, 0])
  })

  it('X3: trägt keine Schicht einen Fehler, fehlt eine Pflichteingabe – die Hochrechnung bleibt offen', () => {
    const current = evaluate(x3, { E19: null, F19: null, G19: null })
    for (const cell of ['E20', 'F22', 'D23', 'D24', 'D25', 'D28', 'D29']) expect(current.cells[cell], cell).toBeNull()
    expect(current.cells.D26).toBeGreaterThan(0)
    expect(current.assumed).toEqual([])
    expect(current.lacking.get('D23')).toEqual(expect.arrayContaining(['E19', 'F19', 'G19']))
  })

  it('X4: Fehler eines Zeitraums leer, der andere trägt einen – mit 0 gerechnet und ausgewiesen', () => {
    const cells = ['C36', 'C37', 'C38', 'C41', 'C42']
    const first = evaluate(x4, { C21: null })
    expect(first.cells.C36).toBe(114800)
    expect(first.assumed).toEqual([{ input: 'C21', cells, kind: 'partialErrorSum' }])
    expect(evaluate(x4, { C34: null }).assumed).toEqual([{ input: 'C34', cells, kind: 'partialErrorSum' }])
    expect(evaluate(x4, { C34: null, C35: null }).assumed.map((entry) => entry.input)).toEqual(['C34', 'C35'])
    const strict = evaluate(x4, { C21: null }, STRICT_POLICY)
    for (const cell of cells) expect(strict.cells[cell], cell).toBeNull()
    expect(strict.cells.C39).toBe(first.cells.C39)
    expect(strict.lacking.get('C36')).toEqual(['C21'])
  })

  it('X4: fehlen die Fehler beider Zeiträume, fehlt eine Pflichteingabe – die Hochrechnung bleibt offen, die Genauigkeit steht', () => {
    const current = evaluate(x4, { C21: null, C34: null })
    for (const cell of ['C36', 'C37', 'C38', 'C41', 'C42']) expect(current.cells[cell], cell).toBeNull()
    expect(current.cells.C39).toBeGreaterThan(0)
    expect(current.assumed).toEqual([])
    expect(current.lacking.get('C36')).toEqual(['C21', 'C34'])
    expect(evaluate(x4, { C21: null, C34: null }, TEMPLATE_POLICY).cells.C36).toBe(0)
  })
})

describe('Wert der Vorlage ohne Grundlage (withoutBasis)', () => {
  it('X3 bei TE = AE: kein Stichprobenumfang, also keine Hochrechnung – die Vorlage zeigt 0 €, 0 % und den Buchwert', () => {
    const current = evaluate(x3, { D11: 0.02 })
    for (const cell of ['D15', 'E17', 'E22', 'D23', 'D24', 'D25', 'D26', 'D28', 'D29']) expect(current.cells[cell], cell).toBeNull()
    expect([current.cells.D1, current.cells.D30]).toEqual([48500000, 47530000])
    for (const cell of ['D23', 'D24', 'D25']) expect(current.lacking.has(cell), cell).toBe(false)
    expect(current.assumed).toEqual([])
    const template = evaluate(x3, { D11: 0.02 }, TEMPLATE_POLICY)
    expect([template.cells.D23, template.cells.D24, template.cells.D25]).toEqual([0, 0, 48500000])
  })

  it('X3 leer: unter „wie die Vorlage“ stehen die Nullen der Vorlage, geltend bleibt jede Summe offen', () => {
    const template = evaluateSheet(x3, {}, createContext({ policy: TEMPLATE_POLICY })).cells
    expect(['D1', 'D3', 'D10', 'D12', 'D14', 'D23', 'D25', 'D30'].map((cell) => template[cell])).toEqual([0, 0, 0, 0, 0, 0, 0, 0])
    const current = evaluateSheet(x3, {}, createContext()).cells
    for (const cell of ['D1', 'D3', 'D10', 'D12', 'D14', 'D23', 'D25', 'D30']) expect(current[cell], cell).toBeNull()
  })

  it('die Abweichungen von X3 gelten für alle zwanzig Schichtspalten', () => {
    const cells = new Set(x3.deviations.map((entry) => entry.cell))
    for (const column of LEGACY_STRATA) for (const line of [17, 20, 22]) expect(cells.has(`${column}${line}`), `${column}${line}`).toBe(true)
    const total = x3.deviations.find((entry) => entry.cell === 'D23' && entry.kind === 'withoutBasis')
    expect(total?.whenEmpty).toEqual(LEGACY_STRATA.map((column) => `${column}22`))
    expect(x3.deviations.find((entry) => entry.cell === 'D15')?.whenEmpty).toEqual(expect.arrayContaining(['E6', 'K8', 'AA7', 'AM8']))
  })
})

describe('Hinweise der Webfassung mit Schichtnummer und zu negativen Umfängen', () => {
  const hints = (sheet: AvailableSheet, changes: Inputs): { id: string; tone: string; text: string }[] => {
    const inputs = { ...sheet.sample.inputs, ...changes }
    return [...(sheet.webHints?.(inputs, sheet.compute(inputs, createContext()), createContext()) ?? [])]
  }

  it('X3: je Schicht mit weniger als drei Einheiten ein Hinweis mit Schichtnummer', () => {
    const small = hints(x3, { H6: 100000, H7: 2, H8: 500, H19: 0, H21: 0, AA6: 100000, AA7: 3, AA8: 500, AA19: 0, AA21: 0 }).filter((hint) => hint.id.startsWith('below-three-units'))
    expect(small).toEqual([
      { id: 'below-three-units-4', tone: 'warning', text: 'Schicht 4: weniger als drei Stichprobeneinheiten (Fußnote der Altvorlage: mindestens 3 je Schicht)' },
      { id: 'below-three-units-8', tone: 'warning', text: 'Schicht 8: weniger als drei Stichprobeneinheiten (Fußnote der Altvorlage: mindestens 3 je Schicht)' },
    ])
    const english = localizeSheet(x3, 'en').texts?.webHints ?? {}
    expect(english['below-three-units-4']).toBe('Stratum 4: fewer than three sampling units (footnote of the legacy template: minimum of 3 per stratum)')
    expect(Object.keys(english).filter((id) => id.startsWith('below-three-units-'))).toHaveLength(LEGACY_STRATA.length)
  })

  it('X4: negativer neu berechneter Umfang wird wie in der Vorlage gezeigt und in Warnfarbe ausgewiesen', () => {
    const negative = evaluate(x4, { C22: 21000 })
    expect(negative.cells.C31).toBe(-11)
    expect(negative.cells.C36).toBeLessThan(0)
    expect(hints(x4, { C22: 21000 }).find((hint) => hint.id === 'negative-denominator')).toMatchObject({ tone: 'warning' })
    expect(hints(x4, {}).map((hint) => hint.id)).toEqual([])
  })

  it('X2 und X3: der Nenner wird quadriert, der Umfang ist nie negativ (mindestens 30)', () => {
    expect(evaluate(x2, { C7: 0.0201 }).cells.C11).toBeGreaterThanOrEqual(30)
    expect(evaluate(x3, { D11: 0.0201 }).cells.D15).toBeGreaterThanOrEqual(30)
    expect(hints(x2, { C7: 0.0201 }).map((hint) => hint.id)).toContain('tolerable-error-not-above-anticipated')
  })
})
