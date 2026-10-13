import { describe, expect, it } from 'vitest'
import { createTranslate } from '../src/i18n/messages'
import { applySubsamples, parsePastedRows, pasteColumns, subsampleTargets } from '../src/model/list'
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
    expect(subsampleTargets(stratified.definition)).toEqual([])
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
    expect(workbook.sheetNames).toEqual(['Ergebnis', sheet.id, '_Arbeitsstand'])
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
})
