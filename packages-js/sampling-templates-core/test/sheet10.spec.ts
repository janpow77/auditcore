import { describe, expect, it } from 'vitest'
import { createTranslate } from '../src/i18n/messages'
import { cellsOf, defaultInputs, fieldsOf, findField, inputFields, named } from '../src/model/definition'
import { evaluateSheet } from '../src/model/evaluate'
import { TEMPLATE_POLICY } from '../src/model/policy'
import { SUMMARY_CELLS, createContext, summaryOf } from '../src/model/sheet'
import { subsampleTargets } from '../src/model/list'
import type { CellMap, CellValue, WebHint } from '../src/model/types'
import { en as shared } from '../src/sheets/01_Parameter/texts.en'
import { NOT_APPLICABLE_GLOBAL } from '../src/sheets/10_SRS_2Z/compute'
import { sheet } from '../src/sheets/10_SRS_2Z/index'
import { en } from '../src/sheets/10_SRS_2Z/texts.en'
import { INCREASE_INTERPRETATION } from '../src/sheets/shared/srs'
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
const PRECISION_CELLS = ['C85', 'C88', 'C89', 'C90', 'C93', 'C94']
const VERDICT_OK = '✔ GFQ und obere Fehlergrenze unter der Schwelle'

const compute = (changes: CellMap = {}): CellMap => sheet.compute({ ...sample, ...changes }, context)
const pick = (results: CellMap, cells: readonly string[]): unknown[] => cells.map((cell) => results[cell] ?? null)
/** Nur der erste Zeitraum ist ausgefüllt. */
const PERIOD_2_EMPTY: CellMap = Object.fromEntries(['C49', 'C50', 'C51', 'C52', 'C53', 'C56', 'C57', 'C77', 'C78', 'C79', 'C80', 'C81'].map((cell) => [cell, null]))

describe('Blatt 10_SRS_2Z', () => {
  it('Beispielwerte ergeben ein vollständiges Ergebnis', () => {
    const result = named(sheet.definition, compute())
    expect(result.randomStratumPopulationPeriod1).toBe(227)
    expect(result.forecastRandomStratumPopulation).toBe(417)
    expect(result.computedSampleSize).toBe(39)
    expect(result.sampleSize).toBe(39)
    expect(result.sampleSizePeriod1).toBe(22)
    expect(result.plannedSampleSizePeriod2).toBe(18)
    expect(result.standardSampleSizePeriod2).toBe(9)
    expect(result.sampleSizePeriod2).toBe(9)
    expect(result.totalSampleSize).toBe(36)
    expect(result.projectedError).toBeCloseTo(269666.67, 2)
    expect(result.precision).toBeCloseTo(187344.75, 2)
    expect(result.totalErrorRate).toBeCloseTo(0.005393, 6)
    expect(result.assessment).toBe(VERDICT_OK)
  })

  it('jede Zelle und jeder Alias kommt genau einmal vor', () => {
    const fields = fieldsOf(sheet.definition)
    expect(new Set(fields.map((field) => field.cell)).size).toBe(fields.length)
    expect(new Set(fields.map((field) => field.alias)).size).toBe(fields.length)
    for (const field of fields) expect(field.alias).toMatch(/^[a-z][A-Za-z0-9]*$/)
  })

  it('der Rechenkern füllt jede Zelle der Definition und die Ergebnisübersicht', () => {
    const cells = Object.keys(compute())
    for (const field of fieldsOf(sheet.definition)) expect(cells).toContain(field.cell)
    for (const cell of Object.values(SUMMARY_CELLS)) expect(cells).toContain(cell)
  })

  it('Vorgaben der Vorlage: zweiseitig, 2 %, Standardneuberechnung, Nein, Nein', () => {
    expect(defaultInputs(sheet.definition)).toEqual({ C20: 'zweiseitig', C23: 0.02, C32: STANDARD, C35: 'Nein', C36: 'Nein' })
  })

  it('Beispielwerte belegen nur Eingabezellen', () => {
    const cells = inputFields(sheet.definition).map((field) => field.cell)
    for (const cell of Object.keys(sample)) expect(cells).toContain(cell)
  })

  it('Buchwert und Anzahl des ersten Zeitraums sind Eingaben, keine Verknüpfung zu Blatt 02', () => {
    expect(fieldsOf(sheet.definition).filter((field) => field.kind === 'link' || field.link)).toEqual([])
    const linked = createContext({ sheets: { '02_Grundgesamtheit': { C51: 1000, C52: 40 } } })
    expect(sheet.compute(defaultInputs(sheet.definition), linked)).toMatchObject({ C7: null, C8: null, C12: null, C13: null })
  })

  it('die Unterstichproben kennen keine Zeiträume: kein Feld übernimmt Summen aus Blatt 17', () => {
    expect(subsampleTargets(sheet.definition)).toEqual([])
  })

  it('die Erhöhung bei begrenztem Umfang ist als Auslegung der Vorlage gekennzeichnet', () => {
    expect(fieldsOf(sheet.definition).filter((field) => field.interpretation).map((field) => field.cell)).toEqual(['C33', 'C39', 'C71', 'C73', 'C94'])
    expect(findField(sheet.definition, 'C71')?.interpretation).toBe(INCREASE_INTERPRETATION)
  })

  it('die Ergebnisübersicht für Blatt 18 liest die festen Zellen N3–N11', () => {
    const results = compute()
    expect(summaryOf(sheet.id, results)).toMatchObject({ sheet: '10_SRS_2Z', method: 'Einfaches Zufallsstichprobenverfahren, 2 Zeiträume', bookValue: 50000000, exhaustiveError: 10500, sampleSize: 36, systemicErrors: 0, anomalousErrors: 0 })
    expect(pick(results, ['N4', 'N5', 'N6', 'N7', 'N10', 'N11'])).toEqual(pick(results, ['C58', 'C84', 'C82', 'C85', 'C74', 'C92']))
  })

  it('Ansatz der Neuberechnung: Standard, Global, Erhöhung und keine Neuberechnung wählen den Umfang für Zeitraum 2', () => {
    const cells = ['C63', 'C70', 'C71', 'C43', 'C72', 'C73', 'C74']
    expect(pick(compute({ C32: STANDARD }), cells)).toEqual([9, 12, 20, 18, 22, 9, 36])
    expect(pick(compute({ C32: GLOBAL }), cells)).toEqual([9, 12, 20, 18, 22, 12, 39])
    expect(pick(compute({ C32: INCREASE }), cells)).toEqual([9, 12, 20, 18, 22, 20, 47])
    expect(pick(compute({ C32: NONE }), cells)).toEqual([9, 12, 20, 18, 22, 18, 45])
    expect(pick(compute({ C32: null }), cells)).toEqual([9, 12, 20, 18, 22, 18, 45])
  })

  it('globale Neuberechnung: Zusatzeinheiten für Zeitraum 1 zählen nur im Ansatz „Global“', () => {
    const cells = ['C66', 'C68', 'C69', 'C70', 'C72', 'C73', 'C74']
    expect(pick(compute({ C32: GLOBAL, C56: 30000 }), cells)).toEqual([228, 228, 100, 107, 122, 107, 234])
    expect(pick(compute({ C32: STANDARD, C56: 30000 }), cells)).toEqual([228, 228, 100, 107, 22, 111, 138])
  })

  it('Erhöhung bei begrenztem Umfang: Faktor über 1 nur, wenn die Ist-Werte die Prognose übersteigen', () => {
    expect(compute({ C32: INCREASE, C49: 31000000 }).C71).toBe(25)
    expect(compute({ C32: INCREASE, C49: 20000000, C50: 170 }).C71).toBe(18)
  })

  it('negativer Nenner: Text der Vorlage in C63; MAX in C73 übergeht ihn, es bleiben die Untergrenzen', () => {
    const cells = ['C63', 'C72', 'C73', 'C74']
    const negative = compute({ C46: 60000 })
    expect(negative.C62).toBeLessThan(0)
    expect(pick(negative, cells)).toEqual([NOT_APPLICABLE_GLOBAL, 22, 3, 30])
    expect(pick(compute({ C46: 60000, C35: 'Ja', C36: 'Ja' }), cells)).toEqual([NOT_APPLICABLE_GLOBAL, 16, 9, 30])
    expect(pick(compute({ C46: 60000, C32: GLOBAL }), cells)).toEqual([NOT_APPLICABLE_GLOBAL, 563, 492, 1060])
    expect(pick(compute({ C46: 60000, C32: INCREASE }), cells)).toEqual([NOT_APPLICABLE_GLOBAL, 22, 20, 47])
    expect(pick(compute({ C46: 60000, C32: NONE }), cells)).toEqual([NOT_APPLICABLE_GLOBAL, 22, 18, 45])
  })

  it('fehlt die Standardabweichung der Variablen q eines Zeitraums, wird mit 0 gerechnet und je Eingabe ausgewiesen', () => {
    const first = compute({ C47: null })
    expect(first.C85).toBeCloseTo(143589.6, 2)
    expect(first.C94).toBe(VERDICT_OK)
    expect(sheet.zeroAssumed?.(first)).toEqual([{ input: 'C47', cells: PRECISION_CELLS }])
    const second = compute({ C80: null })
    expect(second.C85).toBeCloseTo(120333.21, 2)
    expect(sheet.zeroAssumed?.(second)).toEqual([{ input: 'C80', cells: PRECISION_CELLS }])
    const both = compute({ C47: null, C80: null })
    expect(both.C85).toBe(0)
    expect(sheet.zeroAssumed?.(both)).toEqual([{ input: 'C47', cells: PRECISION_CELLS }, { input: 'C80', cells: PRECISION_CELLS }])
    expect(sheet.zeroAssumed?.(compute())).toEqual([])
    expect(sheet.zeroAssumed?.(compute({ C47: null, C29: null }))).toEqual([])
  })

  it('Standardabweichungen für den Umfang (C29, C30, C56) und für Neuberechnungen (C46, C79) sind kein Fall für „mit 0 berechnet“', () => {
    for (const cell of ['C29', 'C30', 'C56', 'C46', 'C79']) expect(sheet.zeroAssumed?.(compute({ [cell]: null }))).toEqual([])
    expect(compute({ C56: null }).C73).toBeNull()
    expect(compute({ C46: null }).C61).toBe(9000)
    expect(compute({ C46: null, C29: null }).C61).toBeNull()
  })

  it('fehlt eine voraussichtliche Standardabweichung, bleiben Umfänge, Genauigkeit und Würdigung offen', () => {
    const results = compute({ C29: null })
    expect(pick(results, ['C31', 'C33', 'C41', 'C42', 'C43', 'C72', 'C73', 'C74', 'C85', 'C88', 'C93', 'C94'])).toEqual(Array(12).fill(null))
    expect(results.C92).toBeCloseTo(0.005393, 6)
    expect(compute({ C29: null, C36: 'Ja' }).C41).toBeNull()
  })

  it('eine Gesamtfehlerquote über der Schwelle wird auch bei offener Genauigkeit gewürdigt', () => {
    expect(compute({ C29: null, C45: 96000 }).C94).toBe('✖ Gesamtfehlerquote über der Signifikanzschwelle')
  })

  it('nur Zeitraum 1 ausgefüllt: geplante Umfänge stehen, die Neuberechnung bleibt offen', () => {
    const cells = ['C42', 'C43', 'C63', 'C70', 'C71', 'C72', 'C73', 'C74', 'C85']
    expect(pick(compute({ ...PERIOD_2_EMPTY }), cells)).toEqual([22, 18, null, null, 18, 22, null, null, null])
    expect(pick(compute({ ...PERIOD_2_EMPTY, C32: GLOBAL }), cells)).toEqual([22, 18, null, null, 18, null, null, null, null])
    expect(pick(compute({ ...PERIOD_2_EMPTY, C32: INCREASE }), cells)).toEqual([22, 18, null, null, 18, 22, 18, 43, null])
    expect(pick(compute({ ...PERIOD_2_EMPTY, C32: NONE }), cells)).toEqual([22, 18, null, null, 18, 22, 18, 43, null])
  })

  it('Hinweise der Webfassung verändern kein Ergebnis', () => {
    const inputs = { ...sample, C19: 0.95, C8: 23, C15: 12, C50: 14, C29: 90000, C30: 90000, C56: 90000 }
    const results = sheet.compute(inputs, context)
    expect(sheet.webHints?.(inputs, results, context).map((hint) => hint.id)).toEqual(['size-exceeds-population-1', 'size-exceeds-population-2', 'confidence-outside-annex'])
    const negative = { ...sample, C46: 60000 }
    expect(sheet.webHints?.(negative, sheet.compute(negative, context), context).map((hint) => hint.id)).toEqual(['negative-denominator'])
    expect(sheet.webHints?.({ ...negative, C32: GLOBAL }, sheet.compute({ ...negative, C32: GLOBAL }, context), context).map((hint) => hint.id)).not.toContain('negative-denominator')
    expect(sheet.webHints?.(sample, compute(), context)).toEqual([])
  })
})

describe('Blatt 10_SRS_2Z: Richtlinie für fehlende Angaben', () => {
  /** Zellen, die das leere Formular zeigen darf – alles andere wäre ein Wert ohne Eingabe. */
  const ALLOWED_WHEN_EMPTY: Record<string, CellValue> = {
    N3: 'Einfaches Zufallsstichprobenverfahren, 2 Zeiträume', // fester Text
    C24: '✔ ≤ 2 %', // Prüfhinweis zur Vorgabe 2 %
    C37: 'Nicht angewandt – Anh. I und II gelten', // Vorgabe „Nein“
    C39: 30, // Mindestumfang der Verordnung; das Feld bezeichnet die Untergrenze selbst
    C82: 0, N6: 0, N8: 0, N9: 0, // freiwillige Einzelbeträge: leer heißt „keine“
  }
  const ZERO_ROWS: string[] = []
  /** „Angabe fehlt“ statt der 0 der Vorlage: Buchwerte und Anzahlen der Zeiträume und was unmittelbar daraus folgt. */
  const LACKING_WHEN_EMPTY = ['C12', 'C13', 'C16', 'C17', 'C25', 'C27', 'C54', 'C55', 'C58', 'N4', 'C59', 'C60', 'C61', 'C64']

  it('leeres Formular: kein Umfang, kein Ergebnis und kein Prüfhinweis ohne Eingabe', () => {
    const inputs = defaultInputs(sheet.definition)
    const evaluation = evaluateSheet(sheet, inputs, context)
    const shown = Object.entries(evaluation.cells).filter(([cell, value]) => value !== null && !(cell in inputs))
    expect(Object.fromEntries(shown.filter(([cell]) => /^[CN]\d+$/.test(cell)))).toEqual(ALLOWED_WHEN_EMPTY)
    expect(shown.filter(([cell]) => !/^[CN]\d+$/.test(cell)).map(([cell, value]) => `${cell.replace(/^[A-Z]+/, '')}=${String(value)}`).filter((entry, index, all) => all.indexOf(entry) === index)).toEqual(ZERO_ROWS)
    expect(evaluation.assumed).toEqual([])
    expect([...evaluation.lacking.keys()]).toEqual(LACKING_WHEN_EMPTY)
  })

  it('Pflichteingabe (requiredInput): „Angabe fehlt“ mit Nennung der Eingabe; wie die Vorlage mit 0 gerechnet und ausgewiesen', () => {
    const inputs = { ...sample, C56: null }
    const current = evaluateSheet(sheet, inputs, context)
    expect(pick(current.cells, ['C63', 'C73', 'C74', 'N10'])).toEqual([null, null, null, null])
    expect(current.lacking.get('C73')).toEqual(['C56'])
    const shown = evaluateSheet(sheet, inputs, likeTemplate)
    expect(pick(shown.cells, ['C63', 'C73', 'C74'])).toEqual([0, 3, 30])
    expect(shown.assumed.map((entry) => entry.input)).toEqual(['C56'])
  })

  it('zweiter Zeitraum leer: kein Ergebnis allein aus dem ersten Zeitraum', () => {
    const current = evaluateSheet(sheet, { ...sample, ...PERIOD_2_EMPTY }, context)
    expect(pick(current.cells, ['C42', 'C43', 'C72'])).toEqual([22, 18, 22])
    expect(pick(current.cells, ['C73', 'C74', 'C83', 'C84', 'C85', 'C88', 'C92', 'C94', 'N4', 'N5', 'N7', 'N10', 'N11'])).toEqual(Array.from({ length: 13 }, () => null))
    expect(current.lacking.get('C74')).toEqual(['C49', 'C50', 'C56'])
  })

  it('Standardabweichung der Stichprobe (sampleDeviation): mit 0 gerechnet und ausgewiesen', () => {
    const current = evaluateSheet(sheet, { ...sample, C80: null }, context)
    expect(current.cells.C85).toBeGreaterThan(0)
    expect(current.assumed).toEqual([{ input: 'C80', cells: PRECISION_CELLS }])
  })

  it('Fehlersumme eines Zeitraums fehlt, der andere trägt eine (partialErrorSum): Ergebnis wie die Vorlage, ausgewiesen', () => {
    const inputs = { ...sample, C78: null }
    const current = evaluateSheet(sheet, inputs, context)
    expect(current.cells.C84).toBeCloseTo(144666.67, 2)
    expect(current.assumed).toEqual([{ input: 'C78', cells: ['C83', 'C84', 'C88', 'C89', 'C91', 'C92', 'C93', 'C94', 'N5', 'N11'], kind: 'partialErrorSum' }])
    expect(current.cells).toEqual(evaluateSheet(sheet, inputs, likeTemplate).cells)
    expect(evaluateSheet(sheet, { ...sample, C45: null }, context).assumed.map((entry) => [entry.input, entry.kind])).toEqual([['C45', 'partialErrorSum']])
  })

  it('Wert ohne Grundlage (withoutBasis): Hochrechnung 0 € ohne Fehlersummen wie die Vorlage gezeigt und ausgewiesen; offen, solange eine Pflichteingabe fehlt', () => {
    const noErrors = { ...sample, C45: null, C78: null }
    const current = evaluateSheet(sheet, noErrors, context)
    expect(current.complete).toBe(true)
    expect(pick(current.cells, ['C83', 'C84'])).toEqual([0, null])
    expect(current.withoutBasis).toEqual(['C83'])
    expect(current.assumed).toEqual([])
    expect(current.lacking.size).toBe(0)
    expect(current.cells).toEqual(evaluateSheet(sheet, noErrors, likeTemplate).cells)
    expect(withoutBasisHint(noErrors)).toEqual({ tone: 'warning', qualified: true })
    // Fehlt dazu die voraussichtliche Fehlerquote (Pflichteingabe), bleibt die Hochrechnung offen – ohne „Angabe fehlt“ an dieser Zelle.
    const incomplete = evaluateSheet(sheet, { ...noErrors, C26: null }, context)
    expect(incomplete.complete).toBe(false)
    expect(pick(incomplete.cells, ['C83', 'C84'])).toEqual([null, null])
    expect(incomplete.withoutBasis).toEqual([])
    expect(incomplete.lacking.has('C83')).toBe(false)
  })

  it('Wert ohne Grundlage (withoutBasis): Umfang aus den bloßen Untergrenzen wie die Vorlage gezeigt und ausgewiesen; offen, solange eine Pflichteingabe fehlt', () => {
    // Ohne Konfidenzniveau ergibt die Standardneuberechnung keinen Umfang; die Vorlage zeigt 3 Einheiten für Zeitraum 2, obwohl 22 geplant waren.
    // Das Konfidenzniveau ist keine Pflichteingabe im Sinne der Abweichungen (die Vorlage zeigt den Umfang selbst nicht mehr).
    const noConfidence = { ...sample, C19: null, C36: 'Ja' }
    const cells = ['C41', 'C42', 'C43', 'C63', 'C72', 'C73', 'C74', 'C75', 'C76', 'N10']
    const shown = [48, 27, 22, null, 27, 3, 35, '✔ ≥ 30 Einheiten', '✔ begrenzter Umfang eingehalten', 35]
    const current = evaluateSheet(sheet, noConfidence, context)
    expect(current.complete).toBe(true)
    expect(pick(current.cells, cells)).toEqual(shown)
    expect(pick(sheet.compute(noConfidence, likeTemplate), cells)).toEqual(shown)
    expect(current.withoutBasis).toEqual(['C73', 'C74', 'C75', 'C76', 'N10'])
    expect(current.lacking.size).toBe(0)
    expect(withoutBasisHint(noConfidence)).toEqual({ tone: 'warning', qualified: true })
    // Fehlt dazu die Standardabweichung des zweiten Zeitraums (Pflichteingabe), bleiben die Untergrenzen offen.
    const incomplete = evaluateSheet(sheet, { ...noConfidence, C56: null }, context)
    expect(incomplete.complete).toBe(false)
    expect(pick(incomplete.cells, cells)).toEqual([48, 27, 22, null, 27, null, null, null, null, null])
    expect(incomplete.withoutBasis).toEqual([])
    expect(withoutBasisHint({ ...noConfidence, C56: null }).tone).toBeUndefined()
  })
})

describe('Blatt 10_SRS_2Z: englische Arbeitsübersetzung', () => {
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
