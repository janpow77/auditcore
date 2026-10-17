import { describe, expect, it } from 'vitest'
import { createTranslate } from '../src/i18n/messages'
import { defaultInputs, fieldsOf, inputCells, inputFields, named } from '../src/model/definition'
import { evaluateSheet } from '../src/model/evaluate'
import { STRICT_POLICY, TEMPLATE_POLICY } from '../src/model/policy'
import { SUMMARY_CELLS, createContext, localizeSheet, summaryOf } from '../src/model/sheet'
import type { CellValue } from '../src/model/types'
import { sheet } from '../src/sheets/05_MUS_2Z/index'
import { isQualified, limitationsOf, type Limitation } from '../src/view/limits'
import { loadGolden, sameValue } from './golden'
import { officialWording } from '../src/model/terms'

const context = createContext()
const GLOBAL = 'Global (Art. 5 Abs. 6 Buchst. b)'
const INCREASE = 'Erhöhung bei begrenztem Umfang (Art. 5 Abs. 7 UAbs. 4 Buchst. a)'
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
const ERROR_CELLS = ['C84', 'C85', 'C89', 'C90', 'C92', 'C93', 'C94', 'C95', 'N5', 'N11']

describe('Blatt 05_MUS_2Z', () => {
  it('Beispielwerte: Umfänge, Hochrechnung und Würdigung', () => {
    const result = named(sheet.definition, compute())
    expect(result).toMatchObject({ sampleSize: 92, sampleSizePeriod1: 50, plannedSampleSizePeriod2: 43, standardSampleSizePeriod2: 20, sampleSizePeriod2: 20, finalSampleSizePeriod1: 50 })
    expect(result.projectedError).toBeCloseTo(463971.63, 2)
    expect(result.precision).toBeCloseTo(280741.72, 2)
    expect(result.totalErrorRate).toBeCloseTo(0.0092794, 7)
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
    expect(defaultInputs(sheet.definition)).toEqual({ C14: 'zweiseitig', C17: 0.02, C26: 'Standard (Art. 5 Abs. 6 Buchst. a)', C29: 'Nein', C30: 'Nein' })
    const cells = inputFields(sheet.definition).map((field) => field.cell)
    for (const cell of Object.keys(sheet.sample.inputs)) expect(cells).toContain(cell)
  })

  it('der Ansatz der Neuberechnung wählt den Umfang für Zeitraum 2', () => {
    expect(compute()).toMatchObject({ C57: 20, C66: 50, C67: 20 })
    expect(compute({ C26: GLOBAL })).toMatchObject({ C63: 23, C62: 0, C66: 50, C67: 23 })
    expect(compute({ C26: INCREASE })).toMatchObject({ C65: 46, C67: 46 })
    expect(compute({ C26: 'keine Neuberechnung' })).toMatchObject({ C35: 43, C67: 43 })
    expect(compute({ C26: null }).C67).toBe(43)
  })

  it('negativer Nenner: Text der Vorlage, kein Umfang im Standardansatz (die Vorlage zeigt die Untergrenzen), Zusatzeinheiten im globalen Ansatz', () => {
    const standard = compute({ C47: 0.9 })
    expect(standard.C57).toBe('✖ nicht anwendbar (Nenner ≤ 0) – globale Neuberechnung')
    expect(standard).toMatchObject({ C66: 50, C67: null, C69: null, C74: null, C85: null, N10: null, N11: null })
    expect(sheet.compute(sample({ C47: 0.9 }), likeTemplate)).toMatchObject({ C66: 50, C67: 3, C69: '✔ ≥ 30 Einheiten', N10: 53 })
    expect(sheet.webHints?.({}, standard, context).map((hint) => hint.id)).toEqual(['negative-denominator'])
    const global = compute({ C47: 0.9, C26: GLOBAL })
    expect(global).toMatchObject({ C62: 1361, C66: 1411, C67: 1302 })
    expect(sheet.webHints?.({}, global, context).map((hint) => hint.id)).toEqual(['size-exceeds-population-1', 'size-exceeds-population-2'])
  })

  it('Auslegung der Vorlage: Faktor und erhöhter Umfang sind gekennzeichnet', () => {
    const marked = fieldsOf(sheet.definition).filter((field) => field.interpretation).map((field) => field.cell)
    expect(marked).toEqual(['C27', 'C40', 'C64', 'C65', 'C95'])
  })

  it('fehlt eine Angabe, bleibt der Umfang offen – auch dort, wo die Vorlage auf den begrenzten Umfang oder die Untergrenzen fiele', () => {
    // Aktualisierte Standardabweichung fehlt: Die Vorlage rechnete n₂ = 0 und zeigte 3 bzw. die Auffüllung auf 30.
    expect(compute({ C50: null })).toMatchObject({ C57: null, C67: null, C69: null, N10: null })
    // Konfidenzniveau fehlt bei begrenztem Umfang: Die Vorlage zeigt 50 Einheiten und für Zeitraum 2 die Untergrenze 3.
    const limited = compute({ C13: null, C30: 'Ja' })
    expect(limited).toMatchObject({ C27: null, C32: 50, C33: null, C34: null, C57: null, C60: null, C67: null, N10: null })
    expect(sheet.webHints?.({}, limited, context).map((hint) => hint.id)).toEqual(['limited-size-open'])
    expect(sheet.compute(sample({ C13: null, C30: 'Ja' }), likeTemplate)).toMatchObject({ C33: 50, C34: 27, C57: null, C67: 3 })
    // „TE ≤ AE“ ist ein Ergebnis, kein fehlender Wert: Der begrenzte Umfang gilt wie in der Vorlage.
    expect(compute({ C20: 0.025, C30: 'Ja' })).toMatchObject({ C27: 'TE ≤ AE', C33: 50, C34: 27 })
    expect(compute({ C13: null })).toMatchObject({ C33: null, C67: null })
  })

  it('leeres Formular: außer festen Texten, der Prüfung der Vorgabe 2 % und den freiwilligen Einzelbeträgen erscheint kein Wert', () => {
    const fixed = { C31: 'Nicht angewandt – Anh. I und II gelten', N3: 'MUS-Standardansatz, 2 Zeiträume', C83: 0, N6: 0, N8: 0, N9: 0 }
    expect(shown(evaluateSheet(sheet, defaultInputs(sheet.definition), context).cells)).toEqual({ ...fixed, C18: '✔ ≤ 2 %' })
    expect(shown(evaluateSheet(sheet, {}, context).cells)).toEqual(fixed)
    expect(sheet.webHints?.({}, sheet.compute({}, context), context)).toEqual([])
    // Die Vorlage zeigt dort Beträge von 0 € und den Faktor 1.
    expect(shown(evaluateSheet(sheet, {}, likeTemplate).cells)).toMatchObject({ C11: 0, C52: 0, C64: 1, N4: 0 })
  })

  it('Pflichteingabe fehlt: „Angabe fehlt“ mit Nennung der Eingabe; wie die Vorlage mit 0 gerechnet und ausgewiesen', () => {
    const current = evaluateSheet(sheet, sample({ C50: null }), context)
    expect(current.cells).toMatchObject({ C57: null, C67: null, N10: null })
    expect(current.lacking.get('C67')).toEqual(['C50'])
    expect(current.assumed).toEqual([])
    const template = evaluateSheet(sheet, sample({ C50: null }), likeTemplate)
    expect(template.cells).toMatchObject({ C57: 0, C67: 3, N10: 53 })
    expect(template.lacking.size).toBe(0)
    expect(template.assumed.find((entry) => entry.input === 'C50')).toMatchObject({ kind: 'requiredInput' })
    expect(template.assumed.find((entry) => entry.input === 'C50')?.cells).toContain('C67')
  })

  it('Faktor der Unterschätzung: Ist-Buchwert und Prognose des zweiten Zeitraums sind Pflichteingaben, die Anzahlen nicht', () => {
    const withoutBookValue = evaluateSheet(sheet, sample({ C48: null, C26: INCREASE }), context)
    expect(withoutBookValue.cells).toMatchObject({ C64: null, C65: null, C67: null })
    expect(withoutBookValue.lacking.get('C64')).toEqual(['C48'])
    // Die Vorlage rechnet den leeren Buchwert als 0 und nimmt allein das Verhältnis der Anzahlen (200 / 190).
    expect(evaluateSheet(sheet, sample({ C48: null, C26: INCREASE }), likeTemplate).cells.C64).toBeCloseTo(200 / 190, 12)
    expect(compute({ C49: null, C10: null }).C64).toBeCloseTo(24000000 / 22500000, 12)
  })

  it('Summe der Fehlerquoten eines Zeitraums fehlt, die des anderen ist eingetragen: wie die Vorlage mit 0 gerechnet und ausgewiesen', () => {
    for (const input of ['C46', 'C81']) {
      const current = evaluateSheet(sheet, sample({ [input]: null }), context)
      expect(current.assumed).toEqual([{ input, cells: ERROR_CELLS, kind: 'partialErrorSum' }])
      expect(current.lacking.size).toBe(0)
      expect(typeof current.cells.C85).toBe('number')
      expect(evaluateSheet(sheet, sample({ [input]: null }), likeTemplate).cells.C85).toBe(current.cells.C85)
      const open = evaluateSheet(sheet, sample({ [input]: null }), strict)
      expect(open.cells).toMatchObject({ C84: null, C85: null, C93: null, C95: null, N5: null, N11: null })
      expect(open.lacking.get('C85')).toEqual([input])
    }
    expect(compute({ C81: null }).C85).toBeCloseTo(5000 + (23600000 / 47) * 0.3, 6)
    // Ohne jede Summe der Fehlerquoten zeigt auch die Vorlage keinen extrapolierten Fehler: nichts auszuweisen.
    const none = evaluateSheet(sheet, sample({ C46: null, C81: null }), context)
    expect(none.cells.C85).toBeNull()
    expect(none.assumed.filter((entry) => entry.kind === 'partialErrorSum')).toEqual([])
  })

  it('Wert ohne Grundlage: bei vollständigen Pflichteingaben wie die Vorlage mit Hinweis in Warnfarbe; offen nur, solange eine Pflichteingabe fehlt', () => {
    // Nenner der Standardneuberechnung nicht positiv: Die Vorlage zeigt die Untergrenze 3 und rechnet damit weiter.
    const inputs = sample({ C47: 0.9 })
    const current = evaluateSheet(sheet, inputs, context)
    expect(current.complete).toBe(true)
    expect(current.cells).toMatchObject({ C67: 3, C69: '✔ ≥ 30 Einheiten', C74: 1, C75: '✖ < 3 Einheiten (Art. 5 Abs. 5)', C95: '✖ Gesamtfehlerquote über der Signifikanzschwelle', N10: 53 })
    expect(current.cells).toEqual(evaluateSheet(sheet, inputs, likeTemplate).cells)
    expect(current.withoutBasis).toEqual(expect.arrayContaining(['C67', 'C74', 'C75', 'C93', 'C95', 'N10']))
    expect(current.lacking.size).toBe(0)
    expect(current.assumed).toEqual([])
    const { limitations, note } = unfoundedNote(inputs)
    expect(note).toMatchObject({ id: 'without-basis', tone: 'warning' })
    expect(isQualified(note ? [note] : [])).toBe(true)
    expect(isQualified(limitations)).toBe(true)
    expect(limitations.find((entry) => entry.id === 'negative-denominator')).toMatchObject({ tone: 'warning', text: expect.stringContaining('wie die Vorlage nur die Untergrenze 3') })
    // Derselbe Fall ohne aktualisierte Standardabweichung (Pflichteingabe): Die Zellen bleiben offen.
    const open = evaluateSheet(sheet, sample({ C47: 0.9, C50: null }), context)
    expect(open.complete).toBe(false)
    expect(open.cells).toMatchObject({ C67: null, C69: null, C74: null, C75: null, C93: null, C95: null, N10: null })
    expect(open.withoutBasis).toEqual([])
    // „Angabe fehlt“ steht an der globalen Neuberechnung, die σ_r2 braucht; die Untergrenze in C67 bleibt als Wert ohne Grundlage offen.
    expect(open.lacking.get('C59')).toEqual(['C50'])
    expect(open.lacking.has('C67')).toBe(false)
    expect(unfoundedNote(sample({ C47: 0.9, C50: null })).note).toBeUndefined()
    // Begrenzter Umfang ohne rechnerischen Umfang (Konfidenzniveau leer): wie die Vorlage 50 Einheiten, die leere Eingabe ist ausgewiesen.
    const limited = evaluateSheet(sheet, sample({ C13: null, C30: 'Ja' }), context)
    expect(limited.cells).toMatchObject({ C27: null, C33: 50, C34: 27, C67: 3 })
    expect(limited.withoutBasis).toEqual(expect.arrayContaining(['C33', 'C34', 'C67']))
    expect(limited.silent).toEqual(['C13'])
    expect(sheet.deviations.filter((entry) => entry.cell === 'C67' && entry.kind === 'withoutBasis')).toHaveLength(2)
  })

  it('fehlt die Standardabweichung der Stichprobe eines Zeitraums, ist ihr Beitrag 0 und wird ausgewiesen', () => {
    const cells = ['C86', 'C89', 'C90', 'C91', 'C94', 'C95']
    expect(sheet.zeroAssumed?.(compute())).toEqual([])
    expect(sheet.zeroAssumed?.(compute({ C47: null }))).toEqual([{ input: 'C47', cells }])
    expect(sheet.zeroAssumed?.(compute({ C82: null }))).toEqual([{ input: 'C82', cells }])
    expect(sheet.zeroAssumed?.(compute({ C47: null, C82: null })).map((entry) => entry.input)).toEqual(['C47', 'C82'])
    expect(compute({ C47: null, C82: null }).C86).toBe(0)
    const open = evaluateSheet(sheet, sample({ C82: null }), strict)
    expect(open.cells).toMatchObject({ C86: null, C94: null })
    expect(open.lacking.get('C86')).toEqual(['C82'])
    expect(evaluateSheet(sheet, sample({ C82: null }), context).lacking.size).toBe(0)
    // Ersatzweise σ für die Neuberechnung (Anh. II Nr. 1.2, Anmerkungen)
    expect(compute({ C47: null }).C55).toBe(0.12)
    // Ohne zweiten Zeitraum gibt es keine Genauigkeit und damit nichts auszuweisen.
    expect(sheet.zeroAssumed?.(compute({ C48: null, C82: null }))).toEqual([])
  })

  it('die Ergebnisübersicht für Blatt 18 liest die festen Zellen N3–N11', () => {
    expect(summaryOf(sheet.id, compute())).toMatchObject({ sheet: '05_MUS_2Z', method: 'MUS-Standardansatz, 2 Zeiträume', bookValue: 50000000, exhaustiveError: 5000, sampleSize: 70, systemicErrors: 0 })
  })

  it('Hinweise der Webfassung verändern kein Ergebnis', () => {
    const inputs = { ...sheet.sample.inputs, C13: 0.95, C49: 10 }
    const results = sheet.compute(inputs, context)
    expect(sheet.webHints?.(inputs, results, context).map((hint) => hint.id)).toEqual(['size-exceeds-population-2', 'confidence-outside-annex'])
    expect(sheet.webHints?.(sheet.sample.inputs, compute(), context)).toEqual([])
  })

  it('unvollständige Belegungen: jeder gezeigte Wert ist der Wert unter der Richtlinie „wie die Vorlage“', () => {
    let seed = 2026101305
    const random = (): number => {
      seed = (seed * 1664525 + 1013904223) % 4294967296
      return seed / 4294967296
    }
    const cells = inputCells(sheet.definition)
    const approaches = sheet.definition.sections.flatMap((section) => section.fields).find((field) => field.cell === 'C26')
    expect(approaches?.list).toBe('recalculation')
    for (let run = 0; run < 400; run += 1) {
      const inputs: Record<string, CellValue> = { ...sheet.sample.inputs, C26: context.parameters.lists.recalculation[run % 4]!, C30: run % 3 ? 'Nein' : 'Ja' }
      for (const cell of cells) if (random() < 0.2) inputs[cell] = null
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
    const produced = new Set(loadGolden(sheet.id).flatMap((golden) => Object.values(golden.erwartet).filter((value): value is string => typeof value === 'string').map((value) => officialWording(value))))
    expect([...produced].filter((value) => !texts?.values?.[value])).toEqual([])
    const hints = [sample({ C47: 0.9 }), sample({ C47: 0.9, C26: GLOBAL }), sample({ C26: GLOBAL, C51: 0.03 }), sample({ C13: 0.95, C9: 10 }), sample({ C13: null, C30: 'Ja' })].flatMap((inputs) => sheet.webHints?.(inputs, sheet.compute(inputs, context), context) ?? [])
    expect(new Set(hints.map((hint) => hint.id))).toEqual(new Set(Object.keys(texts?.webHints ?? {})))
    expect(localizeSheet(sheet, 'en').definition.title).toBe('MUS standard approach – two sampling periods, non-stratified')
  })
})
