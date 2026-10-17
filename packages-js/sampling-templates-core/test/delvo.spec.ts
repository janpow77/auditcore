/**
 * DelVO-Abgleich vom 17.10.2026: amtlicher Begriff „Signifikanzschwelle“ und
 * Hinweise in Warnfarbe, wo die Vorlage von der DelVO (EU) 2023/67 abweicht
 * (Nr. 1–5). Die Hinweise stehen am Ergebnis, in Blatt 18, im Bericht und im
 * Export, deutsch und englisch. Kein Rechenwert ändert sich.
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
  it('Nr. 2: globale Neuberechnung bei AE ≥ TE (05, 07, 10)', async () => {
    const text = await expectCarried(stateWith(sheetOf('05_MUS_2Z'), { C26: GLOBAL, C51: 0.03 }), 'global-te-not-above-ae', '05')
    expect(text).toMatch(/^Berechnet nach DelVO \(EU\) 2023\/67, Anhang II: .*Die Vorlage rechnet hier anders \(/)
    expect((await trace(stateWith(sheetOf('05_MUS_2Z'), { C26: GLOBAL }))).method.map((hint) => hint.id)).not.toContain('global-te-not-above-ae')
    expect((await trace(stateWith(sheetOf('07_MUS_3Z'), { C28: GLOBAL, C57: 0.03 }))).method.map((hint) => hint.id)).toContain('global-te-not-above-ae-2')
    await expectCarried(stateWith(sheetOf('10_SRS_2Z'), { C32: GLOBAL, C57: 0.03 }), 'global-te-not-above-ae', '10')
  })

  it('Nr. 2 nach DelVO: bei AE ≥ TE ist die globale Neuberechnung nicht anwendbar, Folgegrößen und Würdigung bleiben offen', () => {
    const sheet = sheetOf('05_MUS_2Z')
    const blocked = sheet.compute({ ...sheet.sample.inputs, C26: GLOBAL, C51: 0.03 }, createContext())
    expect(blocked.C59).toBe('✖ nicht anwendbar: der voraussichtliche Fehler muss kleiner sein als der zulässige Fehler (Anhang II)')
    expect(['C60', 'C61', 'C62', 'C63', 'C66', 'C67', 'C85', 'C86', 'C93', 'C95', 'N10'].map((cell) => blocked[cell] ?? null)).toEqual(Array(11).fill(null))
    // AE < TE: Formel wie in der Vorlage, (z·BV·σ_w/(TE − AE))² aufgerundet.
    const applied = sheet.compute({ ...sheet.sample.inputs, C26: GLOBAL }, createContext())
    const [z, bookValue, deviation, tolerable, anticipated] = ['C15', 'C52', 'C58', 'C53', 'C54'].map((cell) => Number(applied[cell]))
    expect(applied.C59).toBe(Math.ceil(((z! * bookValue! * deviation!) / (tolerable! - anticipated!)) ** 2))
    // Erster Zeitraum: dieselbe Bedingung, dort mit dem Text der Vorlage „TE ≤ AE“.
    expect(sheet.compute({ ...sheet.sample.inputs, C20: 0.03 }, createContext()).C27).toBe('TE ≤ AE')
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

  it('Nr. 1 und Nr. 4 in Blatt 18: Ersetzung bei Tabelle 2, ein Faktor bei geschichteten Verfahren', async () => {
    const replaced = await trace(stateWith(sheetOf('09_SRS_1Z_S'), {}, REPLACEMENT))
    const precision = textOf(replaced.sheet18, 'replacement-precision-not-scaled')
    expect(precision).toMatch(/^Berechnet nach DelVO \(EU\) 2023\/67, Anhang III Tabelle 2 \(Ersetzung\): .*Die Vorlage rechnet hier anders \(/)
    const factor = textOf(replaced.sheet18, 'stratified-single-factor')
    expect(factor).toContain('„BV(h) ursprünglich“ / „BV(h) reduziert“')
    for (const text of [precision, factor]) {
      expect(replaced.print.map((hint) => hint.text)).toContain(`Blatt 18: ${text}`)
      expect(replaced.export18).toContain(text)
      expect(replaced.exportReport).toContain(`Blatt 18: ${text}`)
    }
    expect((await trace(stateWith(sheetOf('08_SRS_1Z'), {}, EXCLUSION))).sheet18.map((hint) => hint.id)).not.toContain('stratified-single-factor')
  })

  it('jeder neue Hinweis hat eine englische Fassung mit der Fundstelle der englischen DelVO', () => {
    const english = (id: string, hint: string): string => sheetOf(id).translations?.en?.webHints?.[hint] ?? ''
    expect(english('05_MUS_2Z', 'global-te-not-above-ae')).toContain('Calculated in accordance with Delegated Regulation (EU) 2023/67, Annex II')
    expect(english('12_SRS_3Z', 'global-te-not-above-ae-3')).toContain('presupposes that the anticipated error is smaller than the tolerable error (AE < TE)')
    expect(english('11_SRS_2Z_S', 'exclusion-reference-population')).toContain('Annex III, Tables 1 and 2')
    expect(english('18_GFQ_AnhIII', 'stratified-single-factor')).toContain('“BV(h) original” / “BV(h) reduced”')
    expect(english('18_GFQ_AnhIII', 'replacement-precision-not-scaled')).toContain('Annex III, Table 2')
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
