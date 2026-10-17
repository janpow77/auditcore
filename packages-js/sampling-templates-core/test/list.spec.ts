import { describe, expect, it } from 'vitest'
import { createTranslate } from '../src/i18n/messages'
import { applySubsamples, parsePastedRows, pasteColumns, subsampleNeeds, subsampleTargets } from '../src/model/list'
import { createContext } from '../src/model/sheet'
import type { CellMap } from '../src/model/types'
import { sheet as method } from '../src/sheets/03_MUS_1Z/index'
import { sheet as stratified } from '../src/sheets/04_MUS_1Z_S/index'
import { sheet } from '../src/sheets/17_Unterstichprobe/index'
import { buildListView } from '../src/view/listView'
import { computeWorkspace, listRows } from '../src/workspace/compute'
import { openWorkspace } from '../src/workspace/open'
import { saveWorkspace } from '../src/workspace/save'
import { emptyWorkspace, type WorkspaceState } from '../src/workspace/types'
import { exportWorkbook, importWorkbook, readWorkbook, writeWorkbook } from '../src/xlsx/index'

const context = createContext()
const t = createTranslate()
const nbsp = (text: string): string => text.replaceAll(String.fromCharCode(160), ' ')

const rows: CellMap[] = [
  { C5: 'A', C6: 250000, C10: 30, C11: 61000, C12: 915, W5: 'Zufallsschicht', W6: 'Variante 1' },
  { C5: 'B', C6: 640000, C15: 30, C21: 0.84, W5: 'Zufallsschicht', W6: 'Variante 2' },
  { C5: 'C', C6: 900000, C10: 20, C11: 50000, C12: 500, W5: 'hochwertige Einheit', W6: 'Variante 1' },
  { C5: 'D', W5: 'Zufallsschicht', W6: 'Variante 1' },
]

describe('Blatt 17: eine Stichprobeneinheit', () => {
  it('rechnet beide Varianten und wählt die maßgebliche', () => {
    const first = sheet.compute(rows[0]!, context)
    expect(first.C13).toBeCloseTo(3750, 6)
    expect(first.C14).toBeCloseTo(0.015, 9)
    expect([first.W7, first.W8]).toEqual([first.C13, first.C14])
    const second = sheet.compute(rows[1]!, context)
    expect(second.C20).toBeCloseTo(640000 / 30, 6)
    expect(second.C22).toBeCloseTo((640000 / 30) * 0.84, 6)
    expect([second.W7, second.W8]).toEqual([second.C22, second.C23])
    expect(second.C13).toBeNull()
  })
})

describe('Liste der Stichprobeneinheiten', () => {
  it('Summen: hochwertige Einheiten mit ihrem Fehler, Zufallsschicht mit Fehlerquote, Fehler und Buchwert', () => {
    const totals = sheet.totals!(rows, context)
    expect(totals.units).toBe(4)
    expect(totals.incomplete).toBe(1)
    expect(totals.highValueErrors).toBeCloseTo(9000, 6)
    expect(totals.errorRateSum).toBeCloseTo(0.015 + 0.028, 9)
    expect(totals.errorSum).toBeCloseTo(3750 + 17920, 6)
    expect(totals.bookValueSum).toBe(890000)
    expect(sheet.totals!([], context)).toMatchObject({ units: 0, highValueErrors: null, errorRateSum: null })
  })

  it('Übernahme schreibt nur die gekennzeichneten Felder des Methodenblatts', () => {
    expect(subsampleTargets(method.definition).map((field) => [field.cell, field.subsample])).toEqual([
      ['C37', 'highValueErrors'],
      ['C38', 'errorRateSum'],
    ])
    const applied = applySubsamples(method, { ...method.sample.inputs }, sheet.totals!(rows, context))
    expect(applied.applied.map((field) => field.cell)).toEqual(['C37', 'C38'])
    expect(applied.inputs.C37).toBeCloseTo(9000, 6)
    expect(applied.inputs.C38).toBeCloseTo(0.043, 9)
    expect(applied.inputs.C7).toBe(48500000)
    const none = applySubsamples(method, method.sample.inputs, sheet.totals!([], context))
    expect(none.applied).toEqual([])
    expect(none.inputs).toEqual(method.sample.inputs)
  })

  it('geschichtetes Verfahren: Übernahme je Schicht, Einheiten ohne Schichtnummer bleiben außen vor', () => {
    expect(subsampleTargets(stratified.definition).map((field) => [field.cell, field.subsample])).toEqual([
      ['D45', 'highValueErrors'],
      ['D46', 'errorRateSum'],
    ])
    expect(subsampleNeeds(stratified.definition)).toEqual({ stratum: true, period: false })
    expect(subsampleNeeds(method.definition)).toEqual({ stratum: false, period: false })
    const unit = (id: string, bookValue: number, errors: number, extra: CellMap): CellMap => ({ C5: id, C6: bookValue, C10: 10, C11: bookValue / 2, C12: errors, W5: 'Zufallsschicht', W6: 'Variante 1', ...extra })
    const units = [
      unit('S1-a', 100000, 500, { W9: 1 }),
      unit('S1-b', 200000, 0, { W9: 1 }),
      unit('S3-a', 300000, 3000, { W9: 3 }),
      unit('S3-hoch', 900000, 9000, { W9: 3, W5: 'hochwertige Einheit' }),
      unit('S9', 100000, 1000, { W9: 9 }),
      unit('ohne Schicht', 100000, 1000, {}),
    ]
    const totals = sheet.totals!(units, context, subsampleNeeds(stratified.definition))
    expect(totals.unassigned).toBe(1)
    expect(totals.groups?.map((group) => [group.stratum, group.period])).toEqual([[1, null], [3, null], [9, null]])
    const applied = applySubsamples(stratified, {}, totals)
    expect(applied.cells).toEqual(['F45', 'D46', 'F46', 'AB46'])
    expect(applied.inputs.D46).toBeCloseTo(0.01, 12)
    expect(applied.inputs.F46).toBeCloseTo(0.02, 12)
    expect(applied.inputs.F45).toBeCloseTo(18000, 6)
    expect(applied.inputs.AB46).toBeCloseTo(0.02, 12)
    expect(applied.inputs.E46).toBeUndefined()
    const view = buildListView(sheet, units, stratified, context, t)
    expect(view).toMatchObject({ transferable: true, unassigned: 1 })
    expect(view.totals.map((total) => total.target)).toEqual(['Summe der Fehler in hochwertigen Einheiten (ΣE_eh) (D45 ff., je Schicht)', 'Summe der Fehlerquoten der Zufallsschicht (Σ E/BV) (D46 ff., je Schicht)'])
    // Ohne Unterscheidung (ungeschichtetes Verfahren) zählt dieselbe Liste vollständig.
    expect(sheet.totals!(units, context).unassigned).toBeUndefined()
  })

  it('mehrere Zeiträume: Übernahme je Zeitraum über das Kennzeichen `period` der Felder', () => {
    const twoPeriods = { ...method, definition: { ...method.definition, sections: method.definition.sections.map((section) => ({ ...section, fields: section.fields.map((field) => (field.subsample ? { ...field, period: 2 } : field)) })) } }
    expect(subsampleNeeds(twoPeriods.definition)).toEqual({ stratum: false, period: true })
    const unit = (period: number | null): CellMap => ({ C5: `Z${period}`, C6: 100000, C10: 10, C11: 50000, C12: 500, W5: 'Zufallsschicht', W6: 'Variante 1', ...(period ? { W10: period } : {}) })
    const totals = sheet.totals!([unit(1), unit(2), unit(2), unit(null)], context, subsampleNeeds(twoPeriods.definition))
    expect(totals.unassigned).toBe(1)
    const applied = applySubsamples(twoPeriods, {}, totals)
    expect(applied.cells).toEqual(['C38'])
    expect(applied.inputs.C38).toBeCloseTo(0.02, 12)
  })

  it('Übersicht: Spalten der Einheiten und Summen für das Methodenblatt', () => {
    const view = buildListView(sheet, rows, method, context, t)
    expect(view.columns).toHaveLength(6)
    expect(view.rows[0]?.map(nbsp)).toEqual(['A', '250.000,00 €', 'Zufallsschicht', 'Variante 1', '3.750,00 €', '0,0150'])
    expect(view.rows[3]?.[4]).toBe('—')
    expect(view.totals.map((total) => [total.role, nbsp(total.value)])).toEqual([
      ['highValueErrors', '9.000,00 €'],
      ['errorRateSum', '0,0430'],
    ])
    expect(view).toMatchObject({ incomplete: 1, transferable: true })
    expect(buildListView(sheet, rows, null, context, t)).toMatchObject({ totals: [], transferable: false })
  })

  it('Einfügen aus Zwischenablage oder CSV: Reihenfolge der Vorlage, deutsche Zahlen', () => {
    expect(pasteColumns(sheet.definition).map((field) => field.cell)).toEqual(['C5', 'C6', 'C7', 'C8', 'C9', 'C10', 'C11', 'C12', 'C15', 'C17', 'C18', 'C19', 'C21'])
    const pasted = parsePastedRows('V-1\t250.000,00\t140\t\t\t30\t61.000,00\t915,00\r\nV-2\t640.000,00\t210\n\n', sheet.definition)
    expect(pasted).toMatchObject({ rejected: 0, dropped: 0 })
    expect(pasted.rows).toEqual([
      { C5: 'V-1', C6: 250000, C7: 140, C10: 30, C11: 61000, C12: 915, W5: 'Zufallsschicht', W6: 'Variante 1' },
      { C5: 'V-2', C6: 640000, C7: 210, W5: 'Zufallsschicht', W6: 'Variante 1' },
    ])
  })

  it('Einfügen mit Kopfzeile aus Zelladressen, nicht lesbare Zellen werden gezählt', () => {
    const pasted = parsePastedRows('C5;C6;C21;W6\nV-3;640000;0,84;Variante 2\nV-4;1.5;abc;Variante 2', sheet.definition)
    expect(pasted.rows[0]).toMatchObject({ C5: 'V-3', C6: 640000, C21: 0.84, W6: 'Variante 2' })
    expect(pasted.rows[1]).toEqual({ C5: 'V-4', W5: 'Zufallsschicht', W6: 'Variante 2' })
    expect(pasted.rejected).toBe(2)
    expect(parsePastedRows('a\nb\nc', sheet.definition, 2)).toMatchObject({ dropped: 1 })
    expect(parsePastedRows('', sheet.definition).rows).toEqual([])
  })
})

describe('Liste im Arbeitsstand und im Excel-Austausch', () => {
  const state: WorkspaceState = { ...emptyWorkspace(), activeMethod: method.id, sheets: { [method.id]: method.sample.inputs, [sheet.id]: rows } }

  it('Rundlauf erhält die Einheiten; das Listenblatt rechnet nicht als Formularblatt', async () => {
    const opened = await openWorkspace((await saveWorkspace(state)).text)
    expect(opened).toMatchObject({ ok: true, notices: [] })
    expect(opened.ok && listRows(opened.state, sheet.id)).toEqual(rows)
    expect(computeWorkspace(state)).not.toHaveProperty(sheet.id)
    expect(listRows(state, method.id)).toEqual([])
  })

  it('fremde Zellen und unpassende Werte einer Einheit werden gemeldet', async () => {
    const file = JSON.parse((await saveWorkspace(state)).text) as { blaetter: Record<string, unknown> }
    file.blaetter[sheet.id] = [{ C5: 'A', C6: 'viel', C99: 1, kennung: 'alt', W5: 'irgendwo' }]
    file.blaetter[method.id] = [{ C7: 1 }]
    const opened = await openWorkspace(JSON.stringify(file))
    expect(opened.ok).toBe(true)
    if (!opened.ok) return
    expect(opened.state.sheets[sheet.id]).toEqual([{ C5: 'A' }])
    expect(opened.state.sheets[method.id]).toEqual({})
    const unknown = opened.notices.find((notice) => notice.kind === 'unknown-fields')
    expect(unknown).toMatchObject({ fields: expect.arrayContaining([`blaetter.${sheet.id}[0].C6`, `blaetter.${sheet.id}[0].C99`, `blaetter.${sheet.id}[0].kennung`, `blaetter.${sheet.id}[0].W5`, `blaetter.${method.id}`]) })
  })

  it('Export: eigenes Blatt mit einer Zeile je Einheit', async () => {
    const workbook = readWorkbook((await exportWorkbook(state)).data)
    expect(workbook.sheetNames).toEqual(['Ergebnis', sheet.id, '18_GFQ_AnhIII', '20_Druck_KOM', '_Arbeitsstand'])
    const values = [...workbook.cells(sheet.id).values()].map((cell) => cell.value)
    expect(values).toEqual(expect.arrayContaining(['A', 'B', 'C', 'D', 250000, 'hochwertige Einheit']))
    expect(values.some((value) => typeof value === 'number' && Math.abs(value - 3750) < 1e-6)).toBe(true)
  })

  it('Import der Vorlage: Blatt 17 ist eine Einheit', () => {
    const template = Array.from({ length: 12 }, (_, index) => [null, null, index === 4 ? { value: 'V-9' } : index === 5 ? { value: 250000 } : null])
    const imported = importWorkbook(writeWorkbook([{ name: sheet.id, rows: template }]))
    expect(imported).toMatchObject({ kind: 'template', filled: [sheet.id], sheets: { [sheet.id]: [{ C5: 'V-9', C6: 250000, W5: 'Zufallsschicht', W6: 'Variante 1' }] } })
    expect(importWorkbook(writeWorkbook([{ name: sheet.id, rows: [[]] }]))).toMatchObject({ filled: [], sheets: { [sheet.id]: [] } })
  })

  it('Import der Vorlage: Kopien des Blatts 17 werden weitere Einheiten; das in Blatt 18 gewählte Methodenblatt wird gemeldet', () => {
    const unit = (id: string, bookValue: number) => Array.from({ length: 12 }, (_, index) => [null, null, index === 4 ? { value: id } : index === 5 ? { value: bookValue } : null])
    const chosen = [[], [], [], [null, null, { value: method.id }]]
    const workbook = writeWorkbook([
      { name: sheet.id, rows: unit('V-1', 100000) },
      { name: `${sheet.id} (2)`, rows: unit('V-2', 200000) },
      { name: `${sheet.id} (3)`, rows: [[]] },
      { name: '18_GFQ_AnhIII', rows: chosen },
    ])
    const imported = importWorkbook(workbook)
    expect(imported).toMatchObject({ kind: 'template', filled: [sheet.id, '18_GFQ_AnhIII'], method: method.id })
    if (imported.kind !== 'template') throw new Error('Vorlage erwartet')
    expect((imported.sheets[sheet.id] as readonly CellMap[]).map((row) => [row.C5, row.C6])).toEqual([['V-1', 100000], ['V-2', 200000]])
    const unknown = importWorkbook(writeWorkbook([{ name: sheet.id, rows: unit('V-1', 1) }, { name: '18_GFQ_AnhIII', rows: [[], [], [], [null, null, { value: 'kein Blatt' }]] }]))
    expect(unknown).toMatchObject({ method: null })
  })
})
