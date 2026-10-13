import { describe, expect, it } from 'vitest'
import { FAMILIES, CATALOG_TEXTS, localizeFamilies } from '../src/catalog/catalog'
import { createTranslate, samplingTemplatesMessages } from '../src/i18n/messages'
import { defaultInputs, fieldsOf } from '../src/model/definition'
import { createContext, localizeSheet } from '../src/model/sheet'
import { PARAMETERS, SHARED_TEXTS } from '../src/sheets/01_Parameter/index'
import { sheet as population } from '../src/sheets/02_Grundgesamtheit/index'
import { sheet as method } from '../src/sheets/03_MUS_1Z/index'
import { sheet as stratified } from '../src/sheets/04_MUS_1Z_S/index'
import { buildGuide } from '../src/view/guide'
import { buildSections } from '../src/view/sheetView'
import { buildSummary } from '../src/view/summaryView'
import { computeWorkspace } from '../src/workspace/compute'
import { emptyWorkspace, type WorkspaceState } from '../src/workspace/types'
import { loadGolden } from './golden'

const t = createTranslate()
const nbsp = (text: string): string => text.replaceAll(String.fromCharCode(160), ' ')

describe('Kontextfluss Blatt 02 → Methodenblatt', () => {
  const state: WorkspaceState = { ...emptyWorkspace(), activeMethod: method.id, sheets: { [population.id]: population.sample.inputs, [method.id]: defaultInputs(method.definition) } }

  it('Blatt 02: Beispielwerte ergeben BV und N der angepassten Grundgesamtheit', () => {
    const results = population.compute(population.sample.inputs, createContext())
    expect(results).toMatchObject({ C17: 0, C22: 48500000, C30: 0, C37: 48500000, C38: 420, C39: 49200000, C51: 48500000, C52: 420, C54: 42 })
    expect(results.C19).toBe('✔ Datenbestand und SFC2021 stimmen überein')
    expect(results.C53).toBe('⚠ 300 Einheiten oder mehr: statistisches Verfahren (Ausnahme Art. 6 Abs. 3)')
  })

  it('BV und N fließen als vorbelegte Verknüpfung in das Methodenblatt', () => {
    const results = computeWorkspace(state)
    expect(results[method.id]).toMatchObject({ C7: 48500000, C8: 420, C16: 970000 })
    const rows = buildSections(method, state.sheets[method.id] as never, results[method.id]!, createContext({ sheets: results }), t).flatMap((section) => [...section.rows])
    expect(rows.find((row) => row.cell === 'C7')).toMatchObject({ inputText: '48.500.000,00', link: { sheet: population.id, overridden: false } })
  })

  it('eine Überschreibung im Methodenblatt hat Vorrang und ist markiert', () => {
    const overridden: WorkspaceState = { ...state, sheets: { ...state.sheets, [method.id]: { ...defaultInputs(method.definition), C7: 40000000 } } }
    const results = computeWorkspace(overridden)
    expect(results[method.id]).toMatchObject({ C7: 40000000, C8: 420 })
    const rows = buildSections(method, overridden.sheets[method.id] as never, results[method.id]!, createContext({ sheets: results }), t).flatMap((section) => [...section.rows])
    expect(rows.find((row) => row.cell === 'C7')?.link).toEqual({ sheet: population.id, overridden: true })
    expect(rows.find((row) => row.cell === 'C8')?.link).toEqual({ sheet: population.id, overridden: false })
  })

  it('ein leeres Blatt 02 liefert keinen Buchwert 0, sondern keinen Wert', () => {
    const results = computeWorkspace({ ...state, sheets: { [method.id]: defaultInputs(method.definition) } })
    expect(results[population.id]).toMatchObject({ C51: null, C52: null })
    expect(results[method.id]).toMatchObject({ C7: null, C8: null })
  })

  it('Blatt 04 gleicht die Summe der Schichten mit Blatt 02 ab', () => {
    const results = computeWorkspace({ ...state, activeMethod: stratified.id, sheets: { [population.id]: population.sample.inputs, [stratified.id]: stratified.sample.inputs } })
    expect(results[stratified.id]?.C11).toBe(0)
  })
})

describe('Wegweiser der Verfahrensauswahl', () => {
  it('ohne Grundgesamtheit: Hinweis und Merksatz aus Blatt 01, keine Empfehlung', () => {
    const guide = buildGuide(population, undefined, PARAMETERS, t)
    expect(guide.lead).toContain('empfiehlt kein Verfahren')
    expect(guide.items).toEqual([{ id: 'limited-size', tone: 'neutral', text: PARAMETERS.notes.limitedSize }])
  })

  it('mit Grundgesamtheit: Wortlaut der Vorlage zu N < 300 und zum Mindestumfang von 10 %', () => {
    const small = population.compute({ ...population.sample.inputs, C24: 251 }, createContext())
    const guide = buildGuide(population, small, PARAMETERS, t)
    expect(nbsp(guide.lead)).toBe('Angepasste Grundgesamtheit: 251 Einheiten, 48.500.000,00 €.')
    expect(guide.items.map((item) => [item.id, item.tone, item.text])).toEqual([
      ['C53', 'success', '✔ weniger als 300 Einheiten: nichtstatistisches Verfahren zulässig (Art. 79 Abs. 2 VO (EU) 2021/1060)'],
      ['C54', 'neutral', 'Mindestumfang bei nichtstatistischem Verfahren (10 % der Einheiten): 26 (Art. 6 Abs. 2 DelVO.)'],
      ['limited-size', 'neutral', 'Begrenzter Stichprobenumfang: 50 Einheiten für Programme der Kategorie 1 oder 2 ohne Art. 83 (Art. 5 Abs. 7); 30 Einheiten bei Art. 83.'],
    ])
    const large = buildGuide(population, population.compute(population.sample.inputs, createContext()), PARAMETERS, t)
    expect(large.items[0]).toMatchObject({ id: 'C53', tone: 'warning' })
  })
})

describe('Arbeitsübersetzung Englisch', () => {
  const en = createTranslate(samplingTemplatesMessages, 'en')

  it('die Oberflächentexte sind vollständig übersetzt', () => {
    const missing = Object.keys(samplingTemplatesMessages.de).filter((key) => !(key in samplingTemplatesMessages.en))
    expect(missing).toEqual([])
    expect(Object.keys(samplingTemplatesMessages.en).filter((key) => !(key in samplingTemplatesMessages.de))).toEqual([])
  })

  for (const sheet of [population, method]) {
    const texts = sheet.translations?.en

    it(`${sheet.id}: jede Bezeichnung, jede Fundstelle und jeder Abschnitt hat eine Übersetzung`, () => {
      const fields = fieldsOf(sheet.definition)
      expect(fields.filter((field) => !texts?.fields?.[field.cell]?.label).map((field) => field.cell)).toEqual([])
      expect(fields.filter((field) => field.hint && !texts?.fields?.[field.cell]?.hint).map((field) => field.cell)).toEqual([])
      expect(sheet.definition.sections.filter((section) => !texts?.sections?.[section.id]?.title).map((section) => section.id)).toEqual([])
    })

    it(`${sheet.id}: jeder Text der Golden-Fälle (Prüfhinweise, Methodenname) hat eine Übersetzung`, () => {
      const values = loadGolden(sheet.id).flatMap((golden) => Object.entries(golden.erwartet))
      const strings = new Set(values.filter(([reference, value]) => reference.startsWith(sheet.id) && typeof value === 'string').map(([, value]) => String(value)))
      expect([...strings].filter((text) => !(text in (texts?.values ?? {})))).toEqual([])
    })
  }

  it('ein übersetztes Blatt behält Zellen und Werte und zeigt englische Texte', () => {
    const localized = localizeSheet(method, 'en', SHARED_TEXTS.en)
    const results = localized.compute(method.sample.inputs, createContext())
    expect(results).toEqual(method.compute(method.sample.inputs, createContext()))
    const rows = buildSections(localized, method.sample.inputs, results, createContext(), en).flatMap((section) => [...section.rows])
    expect(rows.find((row) => row.cell === 'C27')).toMatchObject({ label: 'Sample size to be applied (at least 30; capped where applicable)', display: '92' })
    expect(rows.find((row) => row.cell === 'C13')).toMatchObject({ display: '✔ average: value between the two minimum levels', value: '✔ mittel: Wert zwischen den Eckwerten' })
    expect(rows.find((row) => row.cell === 'C9')?.options.map((option) => [option.value, option.label])).toEqual([['hoch', 'high'], ['mittel', 'average'], ['gering', 'low']])
    expect(nbsp(rows.find((row) => row.cell === 'C10')?.options.at(-1)?.label ?? '')).toBe('95 % (outside Annex I)')
    const summary = buildSummary(localized, method.sample.inputs, results, createContext(), en)
    expect(summary).toMatchObject({ primaryLabel: 'Sample size to be applied', primaryUnit: 'units' })
    expect(summary.hints[0]?.text).toBe('✔ average: value between the two minimum levels')
    expect(localizeSheet(method, 'de')).toBe(method)
    expect(localizeSheet(stratified, 'en', SHARED_TEXTS.en).definition.title).toBe('MUS standard approach – one sampling period, stratified')
  })

  it('der Wegweiser und der Katalog folgen der Sprache', () => {
    const localized = localizeSheet(population, 'en', SHARED_TEXTS.en)
    const guide = buildGuide(localized, population.compute({ ...population.sample.inputs, C24: 251 }, createContext()), PARAMETERS, en)
    expect(guide.items.map((item) => item.text)).toEqual([
      '✔ fewer than 300 units: non-statistical method admissible (Art. 79(2) of Regulation (EU) 2021/1060)',
      'Minimum coverage for a non-statistical method (10 % of units): 26 (Art. 6(2) DR.)',
      'Capped sample size: 50 sampling units for programmes assessed in category 1 or 2 without Art. 83 (Art. 5(7)); 30 sampling units under Art. 83.',
    ])
    const families = localizeFamilies(FAMILIES, 'en')
    expect(families[0]).toMatchObject({ id: 'mus', name: 'MUS standard approach' })
    expect(families[0]?.variants[0]).toMatchObject({ sheet: '03_MUS_1Z', name: 'MUS standard approach, one period', template2017: 'Template 2' })
    expect(families[0]?.gaps?.[0]?.note).toContain('Annex II points 1.3 and 2.3')
    expect(localizeFamilies(FAMILIES, 'de')).toBe(FAMILIES)
    for (const family of FAMILIES) {
      expect(CATALOG_TEXTS.en.families[family.id]?.name, family.id).toBeTruthy()
      for (const variant of family.variants) expect(CATALOG_TEXTS.en.variants[variant.sheet]?.name, variant.sheet).toBeTruthy()
    }
  })
})
