import { describe, expect, it } from 'vitest'
import { createTranslate } from '../src/i18n/messages'
import { cellsOf, defaultInputs, fieldsOf, inputFields } from '../src/model/definition'
import { evaluateSheet } from '../src/model/evaluate'
import { TEMPLATE_POLICY } from '../src/model/policy'
import { createContext } from '../src/model/sheet'
import type { CellMap, CellValue, WebHint } from '../src/model/types'
import { en as shared } from '../src/sheets/01_Parameter/texts.en'
import { sheet } from '../src/sheets/11_SRS_2Z_S/index'
import { en } from '../src/sheets/11_SRS_2Z_S/texts.en'
import { isQualified, limitationsOf } from '../src/view/limits'
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
const NONE = 'keine Neuberechnung'
/** Zeilen mit Eingaben je Schicht. */
const INPUT_ROWS = ['11', '12', '13', '14', '29', '30', '49', '50', '51', '52', '57', '58', '59', '84', '85', '86', '87']
/** Berechnete Schichtzeilen. */
/** Hohe Standardabweichung der Stichprobe in Zeitraum 1: Der Nenner des Standardansatzes wird negativ. */
const PRECISION_CELLS = ['C93', 'C96', 'C97', 'C98', 'C101', 'C102']
const nulls = (count: number): null[] => Array.from({ length: count }, () => null)

/** Hinweis „wie in der Vorlage gezeigt, obwohl die Grundlage fehlt“ zu den Eingaben – in Warnfarbe, die Würdigung ist dann nicht uneingeschränkt grün. */
function withoutBasisHint(inputs: CellMap): { tone?: string; qualified: boolean } {
  const limitations = limitationsOf(sheet, inputs, evaluateSheet(sheet, inputs, context).cells, context, t)
  return { tone: limitations.find((entry) => entry.kind === 'withoutBasis')?.tone, qualified: isQualified(limitations) }
}

/** Dieselben Werte einer Schicht in eine andere Spalte verschoben. */
function moved(inputs: Inputs, from: string, to: string): Inputs {
  const result: Inputs = { ...inputs }
  for (const row of INPUT_ROWS) {
    result[`${to}${row}`] = inputs[`${from}${row}`] ?? null
    result[`${from}${row}`] = null
  }
  return result
}

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
  })

  it('keine Schicht trägt eine Fehlersumme (withoutBasis): Hochrechnung 0 € wie die Vorlage gezeigt und ausgewiesen; offen, solange eine Pflichteingabe fehlt', () => {
    const inputs = { ...sample, D50: null, E50: null, F50: null, D85: null, E85: null, F85: null }
    // Nichts wurde „mit 0 berechnet“ (keine andere Schicht trägt eine Fehlersumme); die Summen 0 der Vorlage stehen als Werte ohne Grundlage.
    const none = evaluateSheet(sheet, inputs, context)
    expect(none.complete).toBe(true)
    expect([none.cells.C50, none.cells.C85, none.cells.D89, none.cells.C89, none.cells.C92]).toEqual([0, 0, 0, 0, null])
    expect(none.withoutBasis).toEqual(['C50', 'C85', 'D89', 'E89', 'F89', 'C89'])
    expect(none.assumed).toEqual([])
    expect(none.lacking.size).toBe(0)
    expect(none.cells).toEqual(evaluateSheet(sheet, inputs, likeTemplate).cells)
    expect(withoutBasisHint(inputs)).toEqual({ tone: 'warning', qualified: true })
    // Fehlt dazu die voraussichtliche Fehlerquote (Pflichteingabe), bleibt die Hochrechnung offen – ohne „Angabe fehlt“ an diesen Zellen.
    const incomplete = evaluateSheet(sheet, { ...inputs, C25: null }, context)
    expect(incomplete.complete).toBe(false)
    expect([incomplete.cells.C50, incomplete.cells.D89, incomplete.cells.C89, incomplete.cells.C92]).toEqual(nulls(4))
    expect(incomplete.withoutBasis).toEqual([])
    expect(['D89', 'C89'].some((cell) => incomplete.lacking.has(cell))).toBe(false)
  })

  it('Wert ohne Grundlage (withoutBasis): bei „TE ≤ AE“ wie die Vorlage gezeigt und ausgewiesen; offen, solange eine Pflichteingabe fehlt', () => {
    const inputs = { ...sample, C25: 0.025, C33: NONE }
    const cells = ['C44', 'D46', 'D77', 'D79', 'C80', 'C93', 'C102']
    const pick = (results: CellMap): unknown[] => cells.map((cell) => results[cell] ?? null)
    // Alle Pflichteingaben liegen vor: Untergrenzen, Genauigkeit 0 und die Würdigung „✔“ stehen wie in der Vorlage – mit Hinweis in Warnfarbe.
    const current = evaluateSheet(sheet, inputs, context)
    expect(current.complete).toBe(true)
    expect(pick(current.cells)).toEqual([0, '✔ ≥ 3', 3, '✔ ≥ 3', 16, 0, '✔ GFQ und obere Fehlergrenze unter der Schwelle'])
    expect(current.cells).toEqual(evaluateSheet(sheet, inputs, likeTemplate).cells)
    for (const cell of cells) expect(current.withoutBasis, cell).toContain(cell)
    expect(current.lacking.size).toBe(0)
    expect(current.assumed).toEqual([])
    expect(withoutBasisHint(inputs)).toEqual({ tone: 'warning', qualified: true })
    // Fehlt dazu σ Zeitraum 1 einer belegten Schicht (Pflichteingabe), bleiben die Werte ohne Grundlage offen – ohne „Angabe fehlt“ an diesen Zellen.
    const incomplete = evaluateSheet(sheet, { ...inputs, E29: null }, context)
    expect(incomplete.complete).toBe(false)
    expect(pick(incomplete.cells)).toEqual(nulls(7))
    expect(incomplete.withoutBasis).toEqual([])
    expect(cells.some((cell) => incomplete.lacking.has(cell))).toBe(false)
    expect(withoutBasisHint({ ...inputs, E29: null }).tone).toBeUndefined()
    // Mit Gesamtumfang ist die Untergrenze 3 für eine erst in Zeitraum 2 belegte Schicht begründet (Art. 5 Abs. 5).
    const founded = evaluateSheet(sheet, { ...sample, G57: 35, G58: 3200000, G59: 11800, C33: NONE }, context)
    expect(founded.cells.G77).toBe(3)
    expect(founded.withoutBasis).not.toContain('G77')
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
