import { describe, expect, it } from 'vitest'
import { createTranslate } from '../src/i18n/messages'
import { cellsOf, defaultInputs, fieldsOf, inputFields, named } from '../src/model/definition'
import { evaluateSheet } from '../src/model/evaluate'
import { TEMPLATE_POLICY } from '../src/model/policy'
import { subsampleTargets } from '../src/model/list'
import { SUMMARY_CELLS, createContext, summaryOf } from '../src/model/sheet'
import type { CellMap, CellValue, WebHint } from '../src/model/types'
import { en as shared } from '../src/sheets/01_Parameter/texts.en'
import { sheet } from '../src/sheets/12_SRS_3Z/index'
import { en } from '../src/sheets/12_SRS_3Z/texts.en'
import { isQualified, limitationsOf } from '../src/view/limits'
import { caseInputs, loadGolden } from './golden'

const context = createContext()
const sample = sheet.sample.inputs
/** Variante „wie die Vorlage“: Werte ohne Grundlage stehen wie in der Vorlage. */
const likeTemplate = createContext({ policy: TEMPLATE_POLICY })
const t = createTranslate()

/** Hinweis „wie in der Vorlage gezeigt, obwohl die Grundlage fehlt“ zu den Eingaben – in Warnfarbe, die Würdigung ist dann nicht uneingeschränkt grün. */
function withoutBasisHint(inputs: CellMap): { tone?: string; qualified: boolean } {
  const limitations = limitationsOf(sheet, inputs, evaluateSheet(sheet, inputs, context).cells, context, t)
  return { tone: limitations.find((entry) => entry.kind === 'withoutBasis')?.tone, qualified: isQualified(limitations) }
}
const STANDARD = 'Standard (Art. 5 Abs. 6 Buchst. a)'
const GLOBAL = 'Global (Art. 5 Abs. 6 Buchst. b)'
const INCREASE = 'Erhöhung bei begrenztem Umfang (Art. 5 Abs. 7 UAbs. 4 Buchst. a)'
const NONE = 'keine Neuberechnung'
const NOT_APPLICABLE = '✖ nicht anwendbar (Nenner ≤ 0)'
/** Zellen des Ergebnisblocks, die von der Genauigkeit abhängen. */
const PRECISION = ['C129', 'C132', 'C133', 'C134', 'C137', 'C138']

const run = (changes: CellMap = {}): CellMap => sheet.compute({ ...sample, ...changes }, context)
const pick = (results: CellMap, cells: readonly string[]): unknown[] => cells.map((cell) => results[cell])

describe('Blatt 12_SRS_3Z', () => {
  it('Beispielwerte ergeben ein vollständiges Ergebnis', () => {
    const result = named(sheet.definition, run())
    expect(result.randomStratumPopulationPeriod1).toBe(177)
    expect(result.forecastRandomStratumPopulation).toBe(437)
    expect(result.computedSampleSize).toBe(43)
    expect([result.sampleSizePeriod1, result.plannedSampleSizePeriod2, result.plannedSampleSizePeriod3]).toEqual([18, 15, 11])
    expect([result.standardRemainingSampleSize, result.sampleSizePeriod2, result.updatedPlannedSampleSizePeriod3]).toEqual([22, 13, 10])
    expect([result.standardSampleSizePeriod3, result.finalSampleSizePeriod1, result.finalSampleSizePeriod2, result.sampleSizePeriod3]).toEqual([7, 18, 13, 7])
    expect(result.totalSampleSize).toBe(44)
    expect(result.checkMinimumSize).toBe('✔ ≥ 30 Einheiten')
    expect(result.bookValue).toBe(48600000)
    expect(result.projectedError).toBeCloseTo(254007.14, 2)
    expect(result.precision).toBeCloseTo(183346.77, 2)
    expect(result.totalErrorRate).toBeCloseTo(0.005226, 6)
    expect(result.upperErrorLimitRate).toBeCloseTo(0.008999, 6)
    expect(result.assessment).toBe('✔ GFQ und obere Fehlergrenze unter der Schwelle')
  })

  it('jede Zelle und jeder Alias kommt genau einmal vor', () => {
    const fields = fieldsOf(sheet.definition)
    expect(fields).toHaveLength(135)
    expect(new Set(fields.map((field) => field.cell)).size).toBe(fields.length)
    expect(new Set(fields.map((field) => field.alias)).size).toBe(fields.length)
    for (const field of fields) expect(field.alias).toMatch(/^[a-z][A-Za-z0-9]*$/)
  })

  it('der Rechenkern füllt jede Zelle der Definition und die Ergebnisübersicht', () => {
    for (const results of [run(), sheet.compute({}, context)]) {
      const cells = Object.keys(results)
      for (const field of fieldsOf(sheet.definition)) expect(cells).toContain(field.cell)
      for (const cell of Object.values(SUMMARY_CELLS)) expect(cells).toContain(cell)
    }
  })

  it('Vorgaben der Vorlage: zweiseitig, 2 %, Standardansatz, Nein, Nein', () => {
    expect(defaultInputs(sheet.definition)).toEqual({ C22: 'zweiseitig', C25: 0.02, C35: STANDARD, C38: 'Nein', C39: 'Nein' })
  })

  it('Beispielwerte belegen nur Eingabezellen', () => {
    const cells = inputFields(sheet.definition).map((field) => field.cell)
    for (const cell of Object.keys(sample)) expect(cells).toContain(cell)
  })

  it('Buchwert und Anzahl des ersten Zeitraums sind gewöhnliche Eingaben ohne Verknüpfung zu Blatt 02', () => {
    expect(fieldsOf(sheet.definition).filter((field) => field.kind === 'link' || field.link)).toEqual([])
    const linked = createContext({ sheets: { '02_Grundgesamtheit': { C51: 1000, C52: 40 } } })
    expect(sheet.compute(defaultInputs(sheet.definition), linked)).toMatchObject({ C12: null, C13: null, C18: null })
  })

  it('die Ergebnisübersicht für Blatt 18 liest die festen Zellen N3–N11', () => {
    const results = run({ C130: 2500, C131: 1200 })
    expect(summaryOf(sheet.id, results)).toMatchObject({ sheet: '12_SRS_3Z', method: 'Einfaches Zufallsstichprobenverfahren, 3 Zeiträume', bookValue: 48600000, exhaustiveError: 6200, sampleSize: 44, systemicErrors: 2500, anomalousErrors: 1200 })
    expect(pick(results, ['N4', 'N5', 'N6', 'N7', 'N10', 'N11'])).toEqual(pick(results, ['C101', 'C128', 'C126', 'C129', 'C119', 'C136']))
  })

  it.each(['C51', 'C90', 'C124'])('fehlt die Standardabweichung der Variablen q in %s, wird mit 0 gerechnet und ausgewiesen', (input) => {
    const results = run({ [input]: null })
    expect(results.C129).toBeGreaterThan(0)
    expect(results.C129).toBeLessThan(183346)
    expect(results.C138).toBe('✔ GFQ und obere Fehlergrenze unter der Schwelle')
    expect(sheet.zeroAssumed?.(results)).toEqual([{ input, cells: PRECISION }])
  })

  it('fehlen alle drei Standardabweichungen der Variablen q, ist die Genauigkeit 0 und jede Eingabe wird einzeln gemeldet', () => {
    const results = run({ C51: null, C90: null, C124: null })
    expect(results.C129).toBe(0)
    expect(sheet.zeroAssumed?.(results)).toEqual(['C51', 'C90', 'C124'].map((input) => ({ input, cells: PRECISION })))
    expect(sheet.zeroAssumed?.(run())).toEqual([])
    // Ist die Genauigkeit offen, weil eine andere Angabe fehlt, gibt es nichts auszuweisen.
    expect(sheet.zeroAssumed?.(run({ C51: null, C99: null }))).toEqual([])
  })

  it('Standard- und globale Neuberechnung führen zu verschiedenen Umfängen', () => {
    const cells = ['C84', 'C85', 'C86', 'C116', 'C117', 'C118', 'C119']
    expect(pick(run({ C35: STANDARD }), cells)).toEqual([13, 10, 18, 18, 13, 7, 44])
    expect(pick(run({ C35: GLOBAL }), cells)).toEqual([14, 11, 18, 18, 14, 10, 48])
    // Die Zwischenzellen beider Ansätze der ersten Neuberechnung hängen nicht von der Auswahl ab.
    for (const cell of ['C72', 'C73', 'C74', 'C77', 'C79', 'C80', 'C81', 'C82', 'C83']) expect(run({ C35: GLOBAL })[cell]).toBe(run({ C35: STANDARD })[cell])
  })

  it('globale Neuberechnung mit Zusatzeinheiten in früheren Zeiträumen', () => {
    const results = run({ C35: GLOBAL, C50: 16000, C62: 15000, C63: 14000, C89: 17000, C99: 16000 })
    expect(pick(results, ['C79', 'C80', 'C81', 'C82', 'C84', 'C85', 'C86'])).toEqual([120, 31, 40, 32, 40, 32, 49])
    expect(pick(results, ['C111', 'C112', 'C113', 'C114', 'C116', 'C117', 'C118', 'C119'])).toEqual([140, 8, 6, 39, 57, 46, 39, 148])
  })

  it('Erhöhung bei begrenztem Umfang: Faktor 1 unter der Prognose, Faktor > 1 darüber', () => {
    expect(pick(run({ C35: INCREASE }), ['C83', 'C84', 'C85', 'C115', 'C118'])).toEqual([15, 15, 11, 12, 12])
    expect(pick(run({ C35: INCREASE, C53: 17600000, C92: 14300000 }), ['C83', 'C84', 'C85', 'C115', 'C118'])).toEqual([17, 17, 11, 13, 13])
    expect(pick(run({ C35: INCREASE, C54: 190, C93: 150 }), ['C83', 'C84', 'C115', 'C118'])).toEqual([19, 19, 15, 15])
    const marked = fieldsOf(sheet.definition).filter((field) => field.interpretation)
    expect(marked.map((field) => field.cell)).toEqual(['C36', 'C42', 'C83', 'C115', 'C118', 'C138'])
  })

  it('keine Neuberechnung: Die geplanten Umfänge aus J gelten weiter', () => {
    const results = run({ C35: NONE })
    expect(pick(results, ['C46', 'C47', 'C84', 'C85', 'C86', 'C116', 'C117', 'C118'])).toEqual([15, 11, 15, 11, 18, 18, 15, 11])
    expect(pick(run({ C35: null }), ['C84', 'C85', 'C118'])).toEqual([15, 11, 11])
  })

  it('negativer Nenner nach Zeitraum 1: Text der Vorlage, Folgezellen leer, Umfang aus den Untergrenzen', () => {
    const results = run({ C50: 25000 })
    expect(results.C71).toBeLessThan(0)
    expect(pick(results, ['C72', 'C73', 'C74', 'C84', 'C85', 'C86', 'C115'])).toEqual([NOT_APPLICABLE, null, null, 3, null, 18, null])
    expect(pick(results, ['C106', 'C116', 'C117', 'C118', 'C119'])).toEqual([NOT_APPLICABLE, 18, 3, 3, 30])
    // Mit einem anderen Ansatz bleibt der Text stehen, wird aber nicht verwendet.
    expect(pick(run({ C50: 25000, C35: GLOBAL }), ['C72', 'C84', 'C85', 'C86'])).toEqual([NOT_APPLICABLE, 52, 42, 64])
  })

  it('negativer Nenner nach Zeitraum 2: Umfang für Zeitraum 3 aus Mindestumfang und Auffüllung auf 30 Einheiten', () => {
    const results = run({ C89: 30000 })
    expect(results.C105).toBeLessThan(0)
    expect(pick(results, ['C106', 'C116', 'C117', 'C118', 'C119'])).toEqual([NOT_APPLICABLE, 18, 13, 3, 40])
    const filled = run({ C31: 2000, C32: 2000, C33: 2000, C50: 1500, C62: 1500, C63: 1500, C89: 30000, C99: 1500 })
    expect(pick(filled, ['C106', 'C116', 'C117', 'C118', 'C119', 'C120'])).toEqual([NOT_APPLICABLE, 11, 3, 10, 30, '✔ ≥ 30 Einheiten'])
  })

  it('fehlt eine voraussichtliche Standardabweichung, bleiben alle Umfänge, Genauigkeit und Würdigung offen', () => {
    const results = run({ C32: null })
    expect(pick(results, ['C34', 'C36', 'C44', 'C45', 'C84', 'C116', 'C118', 'C119', 'C120', ...PRECISION])).toEqual(Array.from({ length: 15 }, () => null))
    expect(results.C128).toBeCloseTo(254007.14, 2)
    expect(results.C136).toBeCloseTo(0.005226, 6)
  })

  it('fehlen die Ist-Werte des dritten Zeitraums, bleibt dessen Neuberechnung offen, die erste nicht', () => {
    const results = run({ C92: null, C93: null, C99: null })
    expect(pick(results, ['C84', 'C85', 'C86'])).toEqual([13, 10, 18])
    expect(pick(results, ['C116', 'C117'])).toEqual([18, 13])
    expect(pick(results, ['C101', 'C105', 'C106', 'C118', 'C119', 'C128', 'C129', 'C136', 'C138', 'N4', 'N10'])).toEqual(Array.from({ length: 11 }, () => null))
  })

  it('ersatzweise σ: Ohne s_e der Stichprobe gilt die voraussichtliche bzw. aktualisierte Standardabweichung', () => {
    expect(pick(run({ C50: null, C89: null }), ['C68', 'C104'])).toEqual([9000, 9200])
    expect(pick(run(), ['C68', 'C104'])).toEqual([8200, 7900])
    expect(pick(run({ C50: null, C31: null }), ['C68', 'C71', 'C72'])).toEqual([null, null, null])
  })

  it('aktualisierte Fehlerquote: leer gilt der Wert aus I bzw. der vorherige Wert', () => {
    expect(pick(run(), ['C67', 'C103'])).toEqual([0.007 * 48200000, 0.007 * 48600000])
    expect(pick(run({ C64: 0.009 }), ['C67', 'C103'])).toEqual([0.009 * 48200000, 0.009 * 48600000])
    expect(pick(run({ C64: 0.009, C100: 0.006 }), ['C67', 'C103'])).toEqual([0.009 * 48200000, 0.006 * 48600000])
  })

  it('eine Gesamtfehlerquote über der Schwelle wird auch bei offener Genauigkeit gewürdigt', () => {
    const results = run({ C99: null, C49: 60000, C88: 41000 })
    expect(results.C129).toBeNull()
    expect(results.C138).toBe('✖ Gesamtfehlerquote über der Signifikanzschwelle')
  })

  it('die Unterstichproben kennen keine Zeiträume: Kein Feld übernimmt Summen aus Blatt 17', () => {
    expect(subsampleTargets(sheet.definition)).toEqual([])
  })

  it('Hinweise der Webfassung verändern kein Ergebnis', () => {
    const inputs = { ...sample, C8: 20, C54: 14, C93: 12, C15: 15, C17: 12, C61: 12, C21: 0.95, C31: 90000, C32: 90000, C33: 90000 }
    const results = sheet.compute(inputs, context)
    const ids = sheet.webHints?.(inputs, results, context).map((hint) => hint.id) ?? []
    expect(ids).toContain('size-exceeds-population-1')
    expect(ids).toContain('confidence-outside-annex')
    const negative = { ...sample, C50: 25000 }
    expect(sheet.webHints?.(negative, sheet.compute(negative, context), context).map((hint) => hint.id)).toEqual(['negative-denominator-2', 'negative-denominator-3'])
    expect(sheet.webHints?.(sample, run(), context)).toEqual([])
    expect(sheet.webHints?.({ ...negative, C35: GLOBAL }, run({ C50: 25000, C35: GLOBAL }), context)).toEqual([])
  })
})

describe('Blatt 12_SRS_3Z: Richtlinie für fehlende Angaben', () => {
  /** Zellen, die das leere Formular zeigen darf – alles andere wäre ein Wert ohne Eingabe. */
  const ALLOWED_WHEN_EMPTY: Record<string, CellValue> = {
    N3: 'Einfaches Zufallsstichprobenverfahren, 3 Zeiträume', // fester Text
    C26: '✔ ≤ 2 %', // Prüfhinweis zur Vorgabe 2 %
    C40: 'Nicht angewandt – Anh. I und II gelten', // Vorgabe „Nein“
    C42: 30, // Mindestumfang der Verordnung; das Feld bezeichnet die Untergrenze selbst
    C126: 0, N6: 0, N8: 0, N9: 0, // freiwillige Einzelbeträge: leer heißt „keine“
  }
  const ZERO_ROWS: string[] = []
  /** „Angabe fehlt“ statt der 0 der Vorlage: Buchwerte und Anzahlen der Zeiträume und was unmittelbar daraus folgt. */
  const LACKING_WHEN_EMPTY = ['C12', 'C13', 'C18', 'C19', 'C27', 'C29', 'C58', 'C59', 'C65', 'C66', 'C67', 'C68', 'C69', 'C75', 'C97', 'C98', 'C101', 'N4', 'C102', 'C103', 'C104', 'C107']

  it('leeres Formular: kein Umfang, kein Ergebnis und kein Prüfhinweis ohne Eingabe', () => {
    const inputs = defaultInputs(sheet.definition)
    const evaluation = evaluateSheet(sheet, inputs, context)
    const shown = Object.entries(evaluation.cells).filter(([cell, value]) => value !== null && !(cell in inputs))
    expect(Object.fromEntries(shown)).toEqual(ALLOWED_WHEN_EMPTY)
    expect(ZERO_ROWS).toEqual([])
    expect(evaluation.assumed).toEqual([])
    expect([...evaluation.lacking.keys()]).toEqual(LACKING_WHEN_EMPTY)
    // Die Vorlage zeigt für Zeitraum 2 die Untergrenze von 3 Einheiten als anzuwendenden und endgültigen Umfang.
    expect(pick(sheet.compute(inputs, likeTemplate), ['C84', 'C117'])).toEqual([3, 3])
  })

  it('Pflichteingabe (requiredInput): „Angabe fehlt“ mit Nennung der Eingabe; wie die Vorlage mit 0 gerechnet und ausgewiesen', () => {
    const inputs = { ...sample, C99: null }
    const current = evaluateSheet(sheet, inputs, context)
    expect(pick(current.cells, ['C106', 'C118', 'C119', 'N10'])).toEqual([null, null, null, null])
    expect(current.lacking.get('C118')).toEqual(['C99'])
    const shown = evaluateSheet(sheet, inputs, likeTemplate)
    expect(shown.cells.C118).toBeGreaterThanOrEqual(3)
    expect(shown.assumed.map((entry) => entry.input)).toEqual(['C99'])
  })

  it('dritter Zeitraum leer: kein Ergebnis allein aus den ersten beiden Zeiträumen', () => {
    const empty = Object.fromEntries(['C92', 'C93', 'C94', 'C95', 'C96', 'C99', 'C121', 'C122', 'C123', 'C124', 'C125'].map((cell) => [cell, null]))
    const current = evaluateSheet(sheet, { ...sample, ...empty }, context)
    expect(pick(current.cells, ['C84', 'C117'])).toEqual([13, 13])
    expect(pick(current.cells, ['C118', 'C119', 'C127', 'C128', 'C129', 'C132', 'C136', 'C138', 'N4', 'N5', 'N7', 'N10', 'N11'])).toEqual(Array.from({ length: 13 }, () => null))
    expect(current.lacking.get('C119')).toEqual(['C92', 'C93', 'C99'])
  })

  it('Standardabweichung der Stichprobe (sampleDeviation): mit 0 gerechnet und ausgewiesen', () => {
    const current = evaluateSheet(sheet, { ...sample, C90: null }, context)
    expect(current.cells.C129).toBeGreaterThan(0)
    expect(current.assumed).toEqual([{ input: 'C90', cells: PRECISION }])
  })

  it('Fehlersumme eines Zeitraums fehlt, ein anderer trägt eine (partialErrorSum): Ergebnis wie die Vorlage, ausgewiesen', () => {
    const inputs = { ...sample, C88: null }
    const current = evaluateSheet(sheet, inputs, context)
    expect(pick(current.cells, ['C127', 'C128'])).toEqual([169250, 175450])
    expect(current.assumed).toEqual([{ input: 'C88', cells: ['C127', 'C128', 'C132', 'C133', 'C135', 'C136', 'C137', 'C138', 'N5', 'N11'], kind: 'partialErrorSum' }])
    expect(current.cells).toEqual(evaluateSheet(sheet, inputs, likeTemplate).cells)
    expect(evaluateSheet(sheet, { ...sample, C49: null, C122: null }, context).assumed.map((entry) => entry.input)).toEqual(['C49', 'C122'])
  })

  it('Wert ohne Grundlage (withoutBasis): Hochrechnung 0 € ohne Fehlersummen wie die Vorlage gezeigt und ausgewiesen; offen, solange eine Pflichteingabe fehlt', () => {
    const noErrors = { ...sample, C49: null, C88: null, C122: null }
    const current = evaluateSheet(sheet, noErrors, context)
    expect(current.complete).toBe(true)
    expect(pick(current.cells, ['C127', 'C128'])).toEqual([0, null])
    expect(current.withoutBasis).toEqual(['C127'])
    expect(current.assumed).toEqual([])
    expect(current.lacking.size).toBe(0)
    expect(current.cells).toEqual(evaluateSheet(sheet, noErrors, likeTemplate).cells)
    expect(withoutBasisHint(noErrors)).toEqual({ tone: 'warning', qualified: true })
    // Fehlt dazu die voraussichtliche Fehlerquote (Pflichteingabe), bleibt die Hochrechnung offen – ohne „Angabe fehlt“ an dieser Zelle.
    const incomplete = evaluateSheet(sheet, { ...noErrors, C28: null }, context)
    expect(incomplete.complete).toBe(false)
    expect(pick(incomplete.cells, ['C127', 'C128'])).toEqual([null, null])
    expect(incomplete.withoutBasis).toEqual([])
    expect(incomplete.lacking.has('C127')).toBe(false)
  })

  it('Wert ohne Grundlage (withoutBasis): Umfang aus der bloßen Untergrenze wie die Vorlage gezeigt und ausgewiesen; offen, solange eine Pflichteingabe fehlt', () => {
    // TE = AE (Vorlage: „TE ≤ AE“): Es gibt keinen Umfang; die Vorlage zeigt für Zeitraum 2 dennoch 3 Einheiten.
    const undetermined = { ...sample, C28: 0.02, C35: NONE }
    const cells = ['C36', 'C44', 'C46', 'C84', 'C113', 'C117', 'C118', 'C119']
    // C113 (Zusatzeinheiten der globalen Neuberechnung nach Zeitraum 2): Bei AE = TE ist der globale Ansatz nicht anwendbar (Division durch null, Nr. 16).
    const shown = ['✖ nicht anwendbar (Division durch null)', null, null, 3, null, 3, null, null]
    const current = evaluateSheet(sheet, undetermined, context)
    expect(current.complete).toBe(true)
    expect(pick(current.cells, cells)).toEqual(shown)
    expect(pick(sheet.compute(undetermined, likeTemplate), cells)).toEqual(shown)
    expect(current.withoutBasis).toEqual(['C84', 'C117'])
    expect(current.lacking.size).toBe(0)
    expect(withoutBasisHint(undetermined)).toEqual({ tone: 'warning', qualified: true })
    // Fehlt dazu die Standardabweichung des dritten Zeitraums (Pflichteingabe), bleibt die Untergrenze offen.
    const incomplete = evaluateSheet(sheet, { ...undetermined, C99: null }, context)
    expect(incomplete.complete).toBe(false)
    expect(pick(incomplete.cells, cells)).toEqual(['✖ nicht anwendbar (Division durch null)', null, null, null, null, null, null, null])
    expect(incomplete.withoutBasis).toEqual([])
    expect(incomplete.lacking.has('C84')).toBe(false)
    expect(withoutBasisHint({ ...undetermined, C99: null }).tone).toBeUndefined()
    // Nicht positiver Nenner des Standardansatzes: Alle Angaben liegen vor, die Untergrenze 3 steht wie in der Vorlage und ist begründet (Hinweis der Webfassung, kein Wert ohne Grundlage).
    const negative = evaluateSheet(sheet, { ...sample, C50: 60000 }, context)
    expect(pick(negative.cells, ['C72', 'C73', 'C84'])).toEqual([NOT_APPLICABLE, null, 3])
    expect(negative.withoutBasis).toEqual([])
  })
})

describe('Blatt 12_SRS_3Z: englische Arbeitsübersetzung', () => {
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
