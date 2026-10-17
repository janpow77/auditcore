/**
 * DelVO-Abgleich vom 17.10.2026: amtlicher Begriff „Signifikanzschwelle“ und
 * Hinweise, wo die Vorlage von der DelVO (EU) 2023/67 bzw. vom KOM-Leitfaden
 * EGESIF_16-0014-01 abweicht (Nr. 1–5). Nr. 1 und Nr. 2 rechnet die Webfassung
 * nach den Vorgaben der KOM (Entscheidung des Inhabers vom 17.10.2026). Die
 * Warnhinweise stehen am Ergebnis, in Blatt 18, im Bericht und im Export,
 * deutsch und englisch.
 */
import { describe, expect, it } from 'vitest'
import { createTranslate } from '../src/i18n/messages'
import { fieldsOf } from '../src/model/definition'
import { createContext, type AvailableSheet } from '../src/model/sheet'
import { OFFICIAL_THRESHOLD_TERM, TEMPLATE_THRESHOLD_TERM, THRESHOLD_TERM_FIRST, officialWording } from '../src/model/terms'
import type { CellMap } from '../src/model/types'
import { availableSheets, findAvailableSheet } from '../src/sheets/registry'
import { limitationsOf } from '../src/view/limits'
import { buildReport } from '../src/view/reportView'
import { buildSummary } from '../src/view/summaryView'
import { computeWorkspace, contextFor } from '../src/workspace/compute'
import { emptyWorkspace, type WorkspaceState } from '../src/workspace/types'
import { exportWorkbook, readWorkbook } from '../src/xlsx/index'

const t = createTranslate()
const sheetOf = (id: string): AvailableSheet => {
  const sheet = findAvailableSheet(id)
  if (!sheet) throw new Error(`Blatt ${id} fehlt`)
  return sheet
}
const population = sheetOf('02_Grundgesamtheit')
const total = sheetOf('18_GFQ_AnhIII')
const report = sheetOf('20_Druck_KOM')
const EXCLUSION: CellMap = { C41: 2, C42: 3, C43: 500000, C49: 'Ausschluss (Art. 3 Abs. 6 Buchst. b)' }
const REPLACEMENT: CellMap = { ...EXCLUSION, C49: 'Ersetzung (Anh. III)' }
const GLOBAL = 'Global (Art. 5 Abs. 6 Buchst. b)'

function stateWith(method: AvailableSheet, changes: CellMap = {}, populationChanges: CellMap = {}): WorkspaceState {
  return {
    ...emptyWorkspace(),
    activeMethod: method.id,
    sheets: { [population.id]: { ...population.sample.inputs, ...populationChanges }, [method.id]: { ...method.sample.inputs, ...changes }, [total.id]: total.sample.inputs, [report.id]: report.sample.inputs },
  }
}

/** Hinweise am Verfahren, in Blatt 18, im Bericht (Druck) und in den Exportblättern. */
async function trace(state: WorkspaceState) {
  const results = computeWorkspace(state)
  const inputs = (id: string): CellMap => (state.sheets[id] as CellMap | undefined) ?? {}
  const hints = (sheet: AvailableSheet) => buildSummary(sheet, inputs(sheet.id), results[sheet.id] ?? {}, contextFor(sheet.id, state, results), t).hints
  const page = buildReport(report, inputs(report.id), results[report.id] ?? {}, contextFor(report.id, state, results), t)
  const workbook = readWorkbook((await exportWorkbook(state, { now: new Date('2026-10-17T09:30:00Z') })).data)
  const texts = (name: string): string[] => [...workbook.cells(name).values()].map((cell) => String(cell.value ?? ''))
  return { method: hints(sheetOf(state.activeMethod ?? '')), sheet18: hints(total), print: page.hints.filter((hint) => hint.printed), export18: texts(total.id), exportReport: texts(report.id), exportMethod: texts('Ergebnis') }
}

const textOf = (hints: readonly { id: string; text: string }[], id: string): string => hints.find((hint) => hint.id === id)?.text ?? ''

/** Der Hinweis des Verfahrens steht dort, in Blatt 18, im Druck des Berichts und im Export – in Warnfarbe. */
async function expectCarried(state: WorkspaceState, id: string, number: string): Promise<string> {
  const found = await trace(state)
  const text = textOf(found.method, id)
  expect(text, `${id} am Verfahren`).toContain('DelVO (EU) 2023/67')
  expect(found.method.find((hint) => hint.id === id)?.tone).toBe('warning')
  const carried = `Blatt ${number}: ${text}`
  expect(found.sheet18.map((hint) => hint.text)).toContain(carried)
  expect(found.print.map((hint) => hint.text)).toContain(carried)
  expect(found.exportMethod).toContain(text)
  expect(found.export18).toContain(carried)
  expect(found.exportReport).toContain(carried)
  return text
}

describe('Amtlicher Begriff: Signifikanzschwelle', () => {
  it('Text mit dem Begriff der Vorlage wird auf den amtlichen umgestellt; andere Werte bleiben', () => {
    expect(officialWording('✖ Gesamtfehlerquote über der Wesentlichkeitsschwelle')).toBe('✖ Gesamtfehlerquote über der Signifikanzschwelle')
    expect([officialWording(0.02), officialWording(null), officialWording(false)]).toEqual([0.02, null, false])
  })

  it('je Blatt nennt die erste Bezeichnung den Begriff der Vorlage in Klammern, alle übrigen nur den amtlichen', () => {
    let sheets = 0
    for (const sheet of availableSheets()) {
      const labels = fieldsOf(sheet.definition).map((field) => field.label)
      const named = labels.filter((label) => label.includes(OFFICIAL_THRESHOLD_TERM))
      expect(labels.filter((label) => label.includes(THRESHOLD_TERM_FIRST)), sheet.id).toHaveLength(named.length ? 1 : 0)
      if (named.length) expect(named[0], sheet.id).toContain(THRESHOLD_TERM_FIRST)
      expect(labels.join(' ').split(TEMPLATE_THRESHOLD_TERM).length - 1, sheet.id).toBe(named.length ? 1 : 0)
      if (named.length) sheets += 1
    }
    expect(sheets).toBe(16)
    expect(fieldsOf(sheetOf('03_MUS_1Z').definition).find((field) => field.cell === 'C14')?.label).toBe('Signifikanzschwelle (Vorlage: Wesentlichkeitsschwelle) (höchstens 2 %)')
  })

  it('englisch bleibt „materiality threshold“ wie in der englischen DelVO', () => {
    const en = sheetOf('03_MUS_1Z').translations?.en
    expect(en?.fields?.C52?.label).toBe('Assessment against the materiality threshold')
    expect(en?.values?.['✖ Gesamtfehlerquote über der Signifikanzschwelle']).toBe('✖ total error rate above the materiality threshold')
    // Nur die englischen Texte; die Schlüssel von `values` sind die deutschen Texte des Rechenkerns.
    const english = (value: unknown): string[] => (typeof value === 'string' ? [value] : value && typeof value === 'object' ? Object.values(value).flatMap(english) : [])
    expect(availableSheets().flatMap((sheet) => english(sheet.translations?.en)).filter((text) => /Signifikanz|Wesentlichkeit|significance threshold/.test(text))).toEqual([])
  })

  it('Excel-Export: Bezeichnungen mit dem amtlichen Begriff', async () => {
    const found = await trace(stateWith(sheetOf('03_MUS_1Z')))
    expect(found.exportMethod.join('\n')).toContain('Signifikanzschwelle')
    expect(found.exportMethod.join('\n')).not.toMatch(/Wesentlichkeitsschwelle(?!\))/)
  })
})

describe('Abweichungen der Vorlage von der DelVO: Hinweise in Warnfarbe', () => {
  it('Nr. 2 nach KOM: globale Neuberechnung bei AE > TE mit |TE − AE| wie die Vorlage, bei AE = TE nicht anwendbar (05, 07, 10)', async () => {
    const sheet = sheetOf('05_MUS_2Z')
    const above = sheet.compute({ ...sheet.sample.inputs, C26: GLOBAL, C51: 0.03 }, createContext())
    const [z, bookValue, deviation, tolerable, anticipated] = ['C15', 'C52', 'C58', 'C53', 'C54'].map((cell) => Number(above[cell]))
    expect(above.C59).toBe(Math.ceil(((z! * bookValue! * deviation!) / (tolerable! - anticipated!)) ** 2))
    const found = await trace(stateWith(sheet, { C26: GLOBAL, C51: 0.03 }))
    expect(found.method.find((hint) => hint.id === 'anticipated-above-tolerable-global')).toMatchObject({ tone: 'neutral' })
    expect(textOf(found.method, 'anticipated-above-tolerable-global')).toContain('nach KOM-Leitfaden EGESIF_16-0014-01, Abschnitt 7.1, S. 183')
    expect(found.sheet18.map((hint) => hint.text).join('\n')).not.toContain('AE > TE')
    // AE = TE: Division durch null – „nicht anwendbar“, Folgegrößen und Würdigung offen, Warnhinweis mit Art. 5 Abs. 7 UAbs. 4 Buchst. a.
    const equal = sheet.compute({ ...sheet.sample.inputs, C26: GLOBAL, C51: 0.02 }, createContext())
    expect(equal.C59).toBe('✖ nicht anwendbar (Division durch null)')
    expect(['C60', 'C61', 'C62', 'C63', 'C66', 'C67', 'C85', 'C86', 'C93', 'C95', 'N10'].map((cell) => equal[cell] ?? null)).toEqual(Array(11).fill(null))
    const text = await expectCarried(stateWith(sheet, { C26: GLOBAL, C51: 0.02 }), 'size-not-applicable-global', '05')
    expect(text).toContain('Art. 5 Abs. 7 UAbs. 4 Buchst. a DelVO')
    expect((await trace(stateWith(sheetOf('07_MUS_3Z'), { C28: GLOBAL, C57: 0.02 }))).method.map((hint) => hint.id)).toContain('size-not-applicable-global')
    await expectCarried(stateWith(sheetOf('10_SRS_2Z'), { C32: GLOBAL, C57: 0.02 }), 'size-not-applicable-global', '10')
  })

  it('Nr. 2 nach KOM im ersten Zeitraum: AE > TE mit |TE − AE| und Hinweis, ab 4 % Empfehlung, AE = TE nicht anwendbar', async () => {
    const sheet = sheetOf('05_MUS_2Z')
    const above = sheet.compute({ ...sheet.sample.inputs, C20: 0.03 }, createContext())
    const [z, bookValue, deviation, tolerable, anticipated] = ['C15', 'C11', 'C25', 'C19', 'C21'].map((cell) => Number(above[cell]))
    expect(above.C27).toBe(Math.ceil(((z! * bookValue! * deviation!) / (anticipated! - tolerable!)) ** 2))
    expect(above.C22).toBe('⚠ AE > TE: Umfang mit der geplanten Genauigkeit |TE − AE| (KOM-Leitfaden EGESIF_16-0014-01, 7.1)')
    const hints = (await trace(stateWith(sheet, { C20: 0.05 }))).method
    expect(hints.filter((hint) => hint.id.startsWith('anticipated-')).map((hint) => [hint.id, hint.tone])).toEqual([
      ['anticipated-above-tolerable', 'neutral'],
      ['anticipated-at-least-4', 'neutral'],
      // Standardansatz (Vorgabe): Die aktualisierte Fehlerquote fehlt, es gilt die erste – derselbe EGESIF-Hinweis (B5).
      ['anticipated-above-tolerable-standard', 'neutral'],
      ['anticipated-at-least-4-standard', 'neutral'],
    ])
    expect(textOf(hints, 'anticipated-above-tolerable-standard')).toContain('Standardneuberechnung')
    expect(textOf(hints, 'anticipated-at-least-4')).toMatch(/^Auslegung der Webfassung – .*4,0 % bei 2 % Schwelle.*ersetzt ihn nicht$/)
    // Auslöser beim Doppelten der Signifikanzschwelle: bei 1 % ab 2 %, bei 2 % ab 4 %.
    const ids = async (changes: CellMap): Promise<string[]> => (await trace(stateWith(sheet, changes))).method.map((hint) => hint.id)
    expect(await ids({ C17: 0.01, C20: 0.02 })).toContain('anticipated-at-least-4')
    expect(await ids({ C17: 0.01, C20: 0.019 })).not.toContain('anticipated-at-least-4')
    expect(await ids({ C20: 0.039 })).not.toContain('anticipated-at-least-4')
    const equal = sheet.compute({ ...sheet.sample.inputs, C20: 0.02 }, createContext())
    expect([equal.C27, equal.C22]).toEqual(['✖ nicht anwendbar (Division durch null)', '✖ TE = AE: Stichprobenumfang nicht bestimmbar (Division durch null)'])
  })

  it('Nr. 3: nicht anwendbare Standardneuberechnung nennt Anhang II und die Untergrenze', async () => {
    const text = await expectCarried(stateWith(sheetOf('05_MUS_2Z'), { C47: 0.9 }), 'negative-denominator', '05')
    expect(text).toContain('Nach Anhang II DelVO (EU) 2023/67 (Anmerkungen zu Nr. 1.2 und 2.2) ist der Standardansatz bei negativem Ergebnis nicht anwendbar')
    expect(text).toContain('mit der Untergrenze weiter')
    expect(sheetOf('05_MUS_2Z').translations?.en?.webHints?.['negative-denominator']).toContain('Annex II to Delegated Regulation (EU) 2023/67 (notes to points 1.2 and 2.2)')
  })

  it('Nr. 5: Ausschluss bei der einfachen Zufallsstichprobe als Auslegungsfrage, nicht beim MUS-Standardansatz', async () => {
    const text = await expectCarried(stateWith(sheetOf('08_SRS_1Z'), {}, EXCLUSION), 'exclusion-reference-population', '08')
    expect(text).toMatch(/^Auslegungsfrage, Ausschluss nach Art\. 80 Abs\. 3: .*Anhang III Tabellen 1 und 2/)
    expect((await trace(stateWith(sheetOf('03_MUS_1Z'), {}, EXCLUSION))).method.map((hint) => hint.id)).not.toContain('exclusion-reference-population')
    expect((await trace(stateWith(sheetOf('08_SRS_1Z')))).method.map((hint) => hint.id)).not.toContain('exclusion-reference-population')
  })

  it('Nr. 1 und Nr. 4 in Blatt 18 nach KOM: Ersetzung bei Tabelle 2 ohne Lage, anteilige Näherung bei geschichteten Verfahren', async () => {
    const replaced = await trace(stateWith(sheetOf('09_SRS_1Z_S'), {}, REPLACEMENT))
    const id = replaced.sheet18.map((hint) => hint.id).find((entry) => entry.startsWith('replacement-'))
    expect(['replacement-precision-reduced', 'replacement-location-missing']).toContain(id)
    const precision = textOf(replaced.sheet18, id ?? '')
    expect(precision).toMatch(/DelVO \(EU\) 2023\/67, Anhang III Tabelle 2.*Die Vorlage rechnet hier anders \(/)
    const approximation = textOf(replaced.sheet18, 'annex-iii-approximation')
    expect(approximation).toContain('KOM-Leitfaden EGESIF_16-0014-01 (Abschnitt 7.10.2)')
    expect(textOf(replaced.method, 'annex-iii-approximation')).toBe(approximation)
    for (const text of [precision, approximation]) {
      expect(replaced.print.map((hint) => hint.text)).toContain(`Blatt 18: ${text}`)
      expect(replaced.export18).toContain(text)
      expect(replaced.exportReport).toContain(`Blatt 18: ${text}`)
    }
    expect((await trace(stateWith(sheetOf('08_SRS_1Z'), {}, EXCLUSION))).sheet18.map((hint) => hint.id)).not.toContain('annex-iii-approximation')
  })

  it('jeder neue Hinweis hat eine englische Fassung mit der Fundstelle', () => {
    const english = (id: string, hint: string): string => sheetOf(id).translations?.en?.webHints?.[hint] ?? ''
    expect(english('05_MUS_2Z', 'anticipated-above-tolerable')).toContain('Commission guidance EGESIF_16-0014-01, section 7.1, p. 183')
    expect(english('12_SRS_3Z', 'size-not-applicable-global-3')).toContain('Art. 5(7), fourth subparagraph, point (a)')
    expect(english('11_SRS_2Z_S', 'exclusion-reference-population')).toContain('Annex III, Tables 1 and 2')
    expect(english('11_SRS_2Z_S', 'annex-iii-approximation')).toContain('EGESIF_16-0014-01 (section 7.10.2)')
    expect(english('18_GFQ_AnhIII', 'replacement-precision-not-scaled')).toContain('Annex III, Table 2')
    expect(english('18_GFQ_AnhIII', 'exclusion-location-missing')).toContain('1.44 % in accordance with the Commission; as in the template 1.49 % without section C, 1.50 % with section C')
    expect(english('05_MUS_2Z', 'anticipated-above-tolerable-standard')).toContain('standard recalculation')
  })

  it('allgemeine Auslegungen stehen am Blatt und reisen nicht mit; die übrigen Auslegungen reisen mit', async () => {
    const found = await trace(stateWith(sheetOf('03_MUS_1Z')))
    const mus = sheetOf('03_MUS_1Z')
    const state = stateWith(mus)
    const results = computeWorkspace(state)
    const own = limitationsOf(mus, mus.sample.inputs, results[mus.id] ?? {}, contextFor(mus.id, state, results), t).filter((entry) => entry.kind === 'interpretation')
    expect(own.map((entry) => [entry.id, entry.local])).toEqual([['interpretation-C21', true], ['interpretation-C32', true], ['interpretation-C52', true]])
    expect(found.sheet18.map((hint) => hint.id).filter((id) => id.startsWith('03_MUS_1Z-interpretation'))).toEqual([])
    expect(found.print.map((hint) => hint.id)).toEqual(['18_GFQ_AnhIII-interpretation-C24'])
    const carried = await trace(stateWith(sheetOf('05_MUS_2Z')))
    expect(carried.sheet18.map((hint) => hint.id)).toEqual(expect.arrayContaining(['05_MUS_2Z-interpretation-C64', '05_MUS_2Z-interpretation-C65']))
  })
})
