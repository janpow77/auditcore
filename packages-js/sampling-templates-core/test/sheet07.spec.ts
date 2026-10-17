import { REPLACED_BY_KOM } from './delvoGolden'
import { describe, expect, it } from 'vitest'
import { createTranslate } from '../src/i18n/messages'
import { defaultInputs, fieldsOf, inputCells, inputFields, named } from '../src/model/definition'
import { evaluateSheet } from '../src/model/evaluate'
import { STRICT_POLICY, TEMPLATE_POLICY } from '../src/model/policy'
import { SUMMARY_CELLS, createContext, localizeSheet, summaryOf } from '../src/model/sheet'
import type { CellValue } from '../src/model/types'
import { sheet } from '../src/sheets/07_MUS_3Z/index'
import { isQualified, limitationsOf, type Limitation } from '../src/view/limits'
import { loadGolden, sameValue } from './golden'
import { officialWording } from '../src/model/terms'

const context = createContext()
const GLOBAL = 'Global (Art. 5 Abs. 6 Buchst. b)'
const INCREASE = 'Erhöhung bei begrenztem Umfang (Art. 5 Abs. 7 UAbs. 4 Buchst. a)'
const NOT_APPLICABLE = '✖ nicht anwendbar (Nenner ≤ 0)'
const likeTemplate = createContext({ policy: TEMPLATE_POLICY })
const strict = createContext({ policy: STRICT_POLICY })
const t = createTranslate()
/** Hinweis „Wert ohne Grundlage“ unter den Einschränkungen der Auswertung. */
function unfoundedNote(inputs: Record<string, CellValue>): { limitations: Limitation[]; note: Limitation | undefined } {
  const limitations = limitationsOf(sheet, inputs, evaluateSheet(sheet, inputs, context).cells, context, t)
  return { limitations, note: limitations.find((entry) => entry.kind === 'withoutBasis') }
}
const sample = (changes: Record<string, CellValue> = {}): Record<string, CellValue> => ({ ...sheet.sample.inputs, ...changes })
const compute = (changes: Record<string, CellValue> = {}): Readonly<Record<string, CellValue>> => sheet.compute(sample(changes), context)
/** Berechnete Zellen mit einem Wert (ohne Eingabezellen). */
function shown(cells: Readonly<Record<string, CellValue>>): Record<string, CellValue> {
  const inputs = inputCells(sheet.definition)
  return Object.fromEntries(Object.entries(cells).filter(([cell, value]) => value !== null && !inputs.includes(cell)))
}
/** Zellen, die von der Summe der Fehlerquoten eines Zeitraums abhängen. */
const ERROR_CELLS = ['C127', 'C128', 'C132', 'C133', 'C135', 'C136', 'C137', 'C138', 'N5', 'N11']

describe('Blatt 07_MUS_3Z', () => {
  it('Beispielwerte: Umfänge, Hochrechnung und Würdigung', () => {
    const result = named(sheet.definition, compute())
    expect(result).toMatchObject({ sampleSize: 92, sampleSizePeriod1: 35, plannedSampleSizePeriod2: 31, plannedSampleSizePeriod3: 28, sampleSizePeriod2: 20, updatedPlannedSampleSizePeriod3: 18, sampleSizePeriod3: 7 })
    expect(result).toMatchObject({ finalSampleSizePeriod1: 35, finalSampleSizePeriod2: 20, projectedError: 628500 })
    expect(result.precision).toBeCloseTo(336018.41, 2)
    expect(result.totalErrorRate).toBeCloseTo(0.0124455, 7)
    expect(result.assessment).toBe('✔ GFQ und obere Fehlergrenze unter der Schwelle')
  })

  it('jede Zelle und jeder Alias kommt genau einmal vor', () => {
    const fields = fieldsOf(sheet.definition)
    expect(new Set(fields.map((field) => field.cell)).size).toBe(fields.length)
    expect(new Set(fields.map((field) => field.alias)).size).toBe(fields.length)
    for (const field of fields) expect(field.alias).toMatch(/^[a-z][A-Za-z0-9]*$/)
  })

  it('der Rechenkern füllt jede Zelle der Definition und die Ergebnisübersicht', () => {
    for (const inputs of [sheet.sample.inputs, {}]) {
      const cells = Object.keys(sheet.compute(inputs, context))
      for (const field of fieldsOf(sheet.definition)) expect(cells).toContain(field.cell)
      for (const cell of Object.values(SUMMARY_CELLS)) expect(cells).toContain(cell)
    }
  })

  it('Vorgaben der Vorlage und Beispielwerte', () => {
    expect(defaultInputs(sheet.definition)).toEqual({ C15: 'zweiseitig', C18: 0.02, C28: 'Standard (Art. 5 Abs. 6 Buchst. a)', C31: 'Nein', C32: 'Nein' })
    const cells = inputFields(sheet.definition).map((field) => field.cell)
    for (const cell of Object.keys(sheet.sample.inputs)) expect(cells).toContain(cell)
  })

  it('der Ansatz der Neuberechnung wählt die Umfänge für die Zeiträume 2 und 3', () => {
    expect(compute()).toMatchObject({ C66: 20, C67: 18, C75: 20, C76: 18, C77: 35, C99: 7, C109: 7 })
    const global = compute({ C28: GLOBAL })
    expect(global).toMatchObject({ C75: global.C72, C76: global.C73, C109: Math.max(global.C105 as number, 3, 30 - (global.C107 as number) - (global.C108 as number)) })
    expect(global.C107).toBe((global.C77 as number) + (global.C103 as number))
    const increase = compute({ C28: INCREASE })
    expect(increase).toMatchObject({ C75: increase.C74, C76: 28, C109: increase.C106 })
    expect(compute({ C28: 'keine Neuberechnung' })).toMatchObject({ C75: 31, C76: 28, C109: 28 })
  })

  it('negativer Nenner nach Zeitraum 1 und nach Zeitraum 2: kein Umfang im Standardansatz (die Vorlage zeigt die Untergrenzen)', () => {
    const first = compute({ C50: 0.9 })
    expect(first).toMatchObject({ C65: NOT_APPLICABLE, C66: null, C67: null, C75: null, C76: null, C82: null, C83: null, C108: null, C109: null, N10: null })
    expect(sheet.compute(sample({ C50: 0.9 }), likeTemplate)).toMatchObject({ C75: 3, C82: 1, C83: '✖ < 3 Einheiten (Art. 5 Abs. 5)', C108: 3 })
    expect(sheet.webHints?.({}, first, context).map((hint) => hint.id)).toContain('negative-denominator-2')
    const second = compute({ C89: 0.9 })
    expect(second).toMatchObject({ C99: NOT_APPLICABLE, C107: 35, C108: 20, C109: null, C111: null, C128: null, N10: null })
    expect(sheet.compute(sample({ C89: 0.9 }), likeTemplate)).toMatchObject({ C109: 3, C111: '✔ ≥ 30 Einheiten', N10: 58 })
    expect(sheet.webHints?.({}, second, context).map((hint) => hint.id)).toEqual(['negative-denominator-3'])
    // Im globalen Ansatz ist der Nenner ohne Belang.
    expect(sheet.webHints?.({}, compute({ C89: 0.9, C28: GLOBAL }), context).map((hint) => hint.id)).not.toContain('negative-denominator-3')
  })

  it('Auslegung der Vorlage: die erhöhten Umfänge sind gekennzeichnet', () => {
    expect(fieldsOf(sheet.definition).filter((field) => field.interpretation).map((field) => field.cell)).toEqual(['C29', 'C43', 'C74', 'C106', 'C138'])
  })

  it('fehlt eine Angabe, bleibt der Umfang offen – auch dort, wo die Vorlage auf den begrenzten Umfang oder die Untergrenzen fiele', () => {
    expect(compute({ C92: null })).toMatchObject({ C99: null, C109: null, C111: null, N10: null })
    expect(compute({ C55: null })).toMatchObject({ C63: null, C65: null, C75: null })
    // Konfidenzniveau fehlt bei begrenztem Umfang: Die Vorlage zeigt 50 Einheiten und für die Zeiträume 2 und 3 die Untergrenzen.
    const limited = compute({ C14: null, C32: 'Ja' })
    expect(limited).toMatchObject({ C29: null, C34: 50, C35: null, C36: null, C70: null, C75: null, C102: null, C109: null, N10: null })
    expect(sheet.webHints?.({}, limited, context).map((hint) => hint.id)).toEqual(['limited-size-open'])
    expect(sheet.compute(sample({ C14: null, C32: 'Ja' }), likeTemplate)).toMatchObject({ C35: 50, C36: 19, C75: 3, C109: 8 })
    // AE = TE ist ein Ergebnis, kein fehlender Wert: Der begrenzte Umfang gilt wie in der Vorlage (dort „TE ≤ AE“).
    expect(compute({ C21: 0.02, C32: 'Ja' })).toMatchObject({ C29: '✖ nicht anwendbar (Division durch null)', C35: 50, C36: 19 })
  })

  it('leeres Formular: außer festen Texten, der Prüfung der Vorgabe 2 % und den freiwilligen Einzelbeträgen erscheint kein Wert', () => {
    const fixed = { C33: 'Nicht angewandt – Anh. I und II gelten', N3: 'MUS-Standardansatz, 3 Zeiträume', C126: 0, N6: 0, N8: 0, N9: 0 }
    expect(shown(evaluateSheet(sheet, defaultInputs(sheet.definition), context).cells)).toEqual({ ...fixed, C19: '✔ ≤ 2 %' })
    expect(shown(evaluateSheet(sheet, {}, context).cells)).toEqual(fixed)
    expect(sheet.webHints?.({}, sheet.compute({}, context), context)).toEqual([])
    // Die Vorlage zeigt dort die Untergrenze 3 für Zeitraum 2 und darauf einen bestandenen Prüfhinweis.
    expect(shown(evaluateSheet(sheet, defaultInputs(sheet.definition), likeTemplate).cells)).toMatchObject({ C75: 3, C82: 3, C83: '✔ ≥ 3 Einheiten', C108: 3, C125: 3, N4: 0 })
  })

  it('Pflichteingabe fehlt: „Angabe fehlt“ mit Nennung der Eingabe; wie die Vorlage mit 0 gerechnet und ausgewiesen', () => {
    const current = evaluateSheet(sheet, sample({ C92: null }), context)
    expect(current.cells).toMatchObject({ C99: null, C109: null, N10: null })
    expect(current.lacking.get('C109')).toEqual(['C92'])
    expect(current.assumed).toEqual([])
    const template = evaluateSheet(sheet, sample({ C92: null }), likeTemplate)
    expect(template.cells).toMatchObject({ C99: 0, C109: 3, N10: 58 })
    expect(template.lacking.size).toBe(0)
    expect(template.assumed.find((entry) => entry.input === 'C92')).toMatchObject({ kind: 'requiredInput' })
  })

  it('Erhöhung bei begrenztem Umfang: Ist-Buchwert und Prognose des Zeitraums sind Pflichteingaben, die Anzahlen nicht', () => {
    const second = evaluateSheet(sheet, sample({ C51: null, C28: INCREASE }), context)
    expect(second.cells).toMatchObject({ C74: null, C75: null })
    expect(second.lacking.get('C74')).toEqual(['C51'])
    const third = evaluateSheet(sheet, sample({ C90: null, C28: INCREASE }), context)
    expect(third.cells).toMatchObject({ C106: null, C109: null })
    expect(third.lacking.get('C106')).toEqual(['C90'])
    // Die Vorlage rechnet den leeren Buchwert als 0 und nimmt allein das Verhältnis der Anzahlen.
    expect(evaluateSheet(sheet, sample({ C51: null, C28: INCREASE }), likeTemplate).cells.C74).toBe(Math.ceil(31 * (160 / 150)))
    expect(compute({ C52: null, C10: null, C28: INCREASE }).C74).toBe(Math.ceil(31 * (17000000 / 16000000)))
  })

  it('Summe der Fehlerquoten eines Zeitraums fehlt, die eines anderen ist eingetragen: wie die Vorlage mit 0 gerechnet und ausgewiesen', () => {
    for (const input of ['C49', 'C88', 'C122']) {
      const current = evaluateSheet(sheet, sample({ [input]: null }), context)
      expect(current.assumed).toEqual([{ input, cells: ERROR_CELLS, kind: 'partialErrorSum' }])
      expect(current.lacking.size).toBe(0)
      expect(typeof current.cells.C128).toBe('number')
      expect(evaluateSheet(sheet, sample({ [input]: null }), likeTemplate).cells.C128).toBe(current.cells.C128)
      const open = evaluateSheet(sheet, sample({ [input]: null }), strict)
      expect(open.cells).toMatchObject({ C127: null, C128: null, C136: null, C138: null, N5: null, N11: null })
      expect(open.lacking.get('C128')).toEqual([input])
    }
    expect(sheet.zeroAssumed?.(compute({ C49: null, C88: null })).map((entry) => entry.input)).toEqual(['C49', 'C88'])
    // Ohne jede Summe der Fehlerquoten zeigt auch die Vorlage keinen extrapolierten Fehler: nichts auszuweisen.
    const none = evaluateSheet(sheet, sample({ C49: null, C88: null, C122: null }), context)
    expect(none.cells.C128).toBeNull()
    expect(none.assumed.filter((entry) => entry.kind === 'partialErrorSum')).toEqual([])
  })

  it('Wert ohne Grundlage: bei vollständigen Pflichteingaben wie die Vorlage mit Hinweis in Warnfarbe; offen nur, solange eine Pflichteingabe fehlt', () => {
    // Nenner der Standardneuberechnung nach Zeitraum 2 nicht positiv: Die Vorlage zeigt die Untergrenze 3 und rechnet damit weiter.
    const inputs = sample({ C89: 0.9 })
    const current = evaluateSheet(sheet, inputs, context)
    expect(current.complete).toBe(true)
    expect(current.cells).toMatchObject({ C99: NOT_APPLICABLE, C109: 3, C111: '✔ ≥ 30 Einheiten', C116: 2, C117: '✖ < 3 Einheiten (Art. 5 Abs. 5)', C138: '✖ Gesamtfehlerquote über der Signifikanzschwelle', N10: 58 })
    expect(typeof current.cells.C136).toBe('number')
    expect(current.cells).toEqual(evaluateSheet(sheet, inputs, likeTemplate).cells)
    expect(current.withoutBasis).toEqual(expect.arrayContaining(['C109', 'C116', 'C117', 'C136', 'C138', 'N10']))
    expect(current.lacking.size).toBe(0)
    expect(current.assumed).toEqual([])
    const { limitations, note } = unfoundedNote(inputs)
    expect(note).toMatchObject({ id: 'without-basis', tone: 'warning' })
    expect(isQualified(note ? [note] : [])).toBe(true)
    expect(isQualified(limitations)).toBe(true)
    expect(limitations.find((entry) => entry.id === 'negative-denominator-3')).toMatchObject({ tone: 'warning', text: expect.stringContaining('wie die Vorlage nur die Untergrenze 3') })
    // Nenner schon nach Zeitraum 1 nicht positiv: Untergrenzen für beide Zeiträume wie in der Vorlage.
    const first = evaluateSheet(sheet, sample({ C50: 0.9 }), context)
    expect(first.cells).toMatchObject({ C65: NOT_APPLICABLE, C75: 3, C82: 1, C83: '✖ < 3 Einheiten (Art. 5 Abs. 5)', C108: 3, C109: 3 })
    expect(first.withoutBasis).toEqual(expect.arrayContaining(['C75', 'C83', 'C109']))
    // Derselbe Fall ohne aktualisierte Standardabweichung des dritten Zeitraums (Pflichteingabe): Die Zellen bleiben offen.
    const open = evaluateSheet(sheet, sample({ C89: 0.9, C92: null }), context)
    expect(open.complete).toBe(false)
    expect(open.cells).toMatchObject({ C109: null, C111: null, C116: null, C117: null, C136: null, C138: null, N10: null })
    expect(open.withoutBasis).toEqual([])
    // „Angabe fehlt“ steht an der globalen Neuberechnung, die σ_r3 braucht; die Untergrenze in C109 bleibt als Wert ohne Grundlage offen.
    expect(open.lacking.get('C101')).toEqual(['C92'])
    expect(open.lacking.has('C109')).toBe(false)
    expect(unfoundedNote(sample({ C89: 0.9, C92: null })).note).toBeUndefined()
  })

  it('fehlt die Standardabweichung der Stichprobe eines Zeitraums, ist ihr Beitrag 0 und wird ausgewiesen', () => {
    const cells = ['C129', 'C132', 'C133', 'C134', 'C137', 'C138']
    expect(sheet.zeroAssumed?.(compute())).toEqual([])
    for (const input of ['C50', 'C89', 'C123']) expect(sheet.zeroAssumed?.(compute({ [input]: null }))).toEqual([{ input, cells }])
    expect(sheet.zeroAssumed?.(compute({ C50: null, C89: null, C123: null })).map((entry) => entry.input)).toEqual(['C50', 'C89', 'C123'])
    // Ersatzweise σ für die Neuberechnungen
    expect(compute({ C50: null }).C61).toBe(0.12)
    expect(compute({ C89: null }).C97).toBe(0.11)
    const open = evaluateSheet(sheet, sample({ C123: null }), strict)
    expect(open.cells).toMatchObject({ C129: null, C137: null })
    expect(open.lacking.get('C129')).toEqual(['C123'])
    expect(evaluateSheet(sheet, sample({ C123: null }), context).lacking.size).toBe(0)
  })

  it('die Ergebnisübersicht für Blatt 18 liest die festen Zellen N3–N11', () => {
    expect(summaryOf(sheet.id, compute())).toMatchObject({ sheet: '07_MUS_3Z', method: 'MUS-Standardansatz, 3 Zeiträume', bookValue: 50500000, exhaustiveError: 6500, sampleSize: 62, anomalousErrors: 0 })
  })

  it('Hinweise der Webfassung verändern kein Ergebnis', () => {
    const inputs = { ...sheet.sample.inputs, C14: 0.95, C52: 10, C91: 5 }
    const results = sheet.compute(inputs, context)
    expect(sheet.webHints?.(inputs, results, context).map((hint) => hint.id)).toEqual(['size-exceeds-population-2', 'size-exceeds-population-3', 'confidence-outside-annex'])
    expect(sheet.webHints?.(sheet.sample.inputs, compute(), context)).toEqual([])
  })

  it('unvollständige Belegungen: jeder gezeigte Wert ist der Wert unter der Richtlinie „wie die Vorlage“', () => {
    let seed = 2026101307
    const random = (): number => {
      seed = (seed * 1664525 + 1013904223) % 4294967296
      return seed / 4294967296
    }
    const cells = inputCells(sheet.definition)
    for (let run = 0; run < 400; run += 1) {
      const inputs: Record<string, CellValue> = { ...sheet.sample.inputs, C28: context.parameters.lists.recalculation[run % 4]!, C32: run % 3 ? 'Nein' : 'Ja' }
      for (const cell of cells) if (random() < 0.15) inputs[cell] = null
      const results = evaluateSheet(sheet, inputs, context, false).cells
      const template = evaluateSheet(sheet, inputs, likeTemplate).cells
      for (const [cell, value] of Object.entries(results)) {
        if (value !== null && !cells.includes(cell)) expect(sameValue(template[cell] ?? null, value), `${cell} Lauf ${run}`).toBe(true)
      }
    }
  })

  it('englische Arbeitsübersetzung: jedes Feld, jede Fundstelle, jeder Abschnitt, jeder Text des Rechenkerns und jeder Hinweis der Webfassung', () => {
    const texts = sheet.translations?.en
    const fields = fieldsOf(sheet.definition)
    expect(fields.filter((field) => !texts?.fields?.[field.cell]?.label).map((field) => field.cell)).toEqual([])
    expect(fields.filter((field) => field.hint && !texts?.fields?.[field.cell]?.hint).map((field) => field.cell)).toEqual([])
    expect(fields.filter((field) => field.interpretation && !texts?.fields?.[field.cell]?.interpretation).map((field) => field.cell)).toEqual([])
    expect(Object.keys(texts?.fields ?? {}).filter((cell) => !fields.some((field) => field.cell === cell))).toEqual([])
    expect(sheet.definition.sections.filter((section) => !texts?.sections?.[section.id]?.title || (section.reference && !texts.sections[section.id]?.reference)).map((section) => section.id)).toEqual([])
    expect(sheet.definition.summary.rows.filter((row) => !texts?.summary?.rows?.[row.cell]).map((row) => row.cell)).toEqual([])
    const produced = new Set(loadGolden(sheet.id).flatMap((golden) => Object.values(golden.erwartet).filter((value): value is string => typeof value === 'string').filter((value) => !REPLACED_BY_KOM.has(value)).map((value) => officialWording(value))))
    expect([...produced].filter((value) => !texts?.values?.[value])).toEqual([])
    const hints = [sample({ C50: 0.9 }), sample({ C89: 0.9 }), sample({ C28: GLOBAL, C57: 0.03, C93: 0.03 }), sample({ C14: 0.95, C52: 10, C91: 5 }), sample({ C14: null, C32: 'Ja' }), sample({ C21: 0.05 }), sample({ C28: GLOBAL, C57: 0.05, C93: 0.05 }), sample({ C28: GLOBAL, C57: 0.02 }), sample({ C28: GLOBAL, C57: 0.03, C93: 0.02 })].flatMap((inputs) => sheet.webHints?.(inputs, sheet.compute(inputs, context), context) ?? [])
    const excluded = createContext({ sheets: { '02_Grundgesamtheit': { C47: 2, C49: 'Ausschluss (Art. 3 Abs. 6 Buchst. b)' } } })
    hints.push(...(sheet.webHints?.(sheet.sample.inputs, sheet.compute(sheet.sample.inputs, excluded), excluded) ?? []))
    expect(new Set(hints.map((hint) => hint.id))).toEqual(new Set(Object.keys(texts?.webHints ?? {})))
    expect(localizeSheet(sheet, 'en').definition.title).toBe('MUS standard approach – three sampling periods, non-stratified')
  })
})
