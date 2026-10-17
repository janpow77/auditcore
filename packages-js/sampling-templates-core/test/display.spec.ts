import { describe, expect, it } from 'vitest'
import { createTranslate } from '../src/i18n/messages'
import { defaultInputs, strataColumnsOf } from '../src/model/definition'
import { evaluateSheet } from '../src/model/evaluate'
import { createContext, type AvailableSheet } from '../src/model/sheet'
import { usedStrata } from '../src/model/strata'
import { SHEETS, availableSheets, findAvailableSheet, tableOf } from '../src/sheets/registry'
import { strataRows } from '../src/view/sheetView'
import { buildSummary, isEmptyForm } from '../src/view/summaryView'
import { buildDataTable } from '../src/view/tableView'
import { exportWorkbook, importWorkbook, readWorkbook } from '../src/xlsx/index'
import { emptyWorkspace } from '../src/workspace/types'

const context = createContext()
const t = createTranslate()
const en = createTranslate(undefined, 'en')
const nbsp = (text: string): string => text.replaceAll(String.fromCharCode(160), ' ')
const sheetOf = (id: string): AvailableSheet => {
  const sheet = findAvailableSheet(id)
  if (!sheet) throw new Error(`Blatt ${id} fehlt`)
  return sheet
}
const summaryOf = (sheet: AvailableSheet, inputs: Record<string, string | number | null>) => buildSummary(sheet, inputs, evaluateSheet(sheet, inputs, context).cells, context, t)

describe('Ergebnisspalte je Blattart', () => {
  it('leeres Formular: „noch keine Angaben“ statt einer Zahl, keine Prüfhinweise – in jedem Blatt', () => {
    for (const sheet of availableSheets().filter((entry) => entry.definition.layout !== 'list')) {
      const inputs = defaultInputs(sheet.definition)
      const cells = evaluateSheet(sheet, inputs, context).cells
      expect(isEmptyForm(sheet, cells), sheet.id).toBe(true)
      const summary = buildSummary(sheet, inputs, cells, context, t)
      expect([sheet.id, summary.primaryValue, summary.primaryNote]).toEqual([sheet.id, '', 'noch keine Angaben'])
      expect(summary.hints, sheet.id).toEqual([])
      expect(summary.gauge, sheet.id).toBeNull()
    }
    expect(en('noEntries')).toBe('no entries yet')
  })

  it('Beispielwerte: jedes Blatt zeigt seine Hauptgröße', () => {
    for (const sheet of availableSheets().filter((entry) => entry.definition.layout !== 'list' && !['18_GFQ_AnhIII', '20_Druck_KOM'].includes(entry.id))) {
      const summary = summaryOf(sheet, sheet.sample.inputs)
      expect(isEmptyForm(sheet, evaluateSheet(sheet, sheet.sample.inputs, context).cells), sheet.id).toBe(false)
      expect(summary.primaryValue, sheet.id).not.toBe('')
    }
  })

  it('Skala: statistisch mit oberer Fehlergrenze, nichtstatistisch ohne, Altvorlagen mit ihren Begriffen', () => {
    const statistical = summaryOf(sheetOf('03_MUS_1Z'), sheetOf('03_MUS_1Z').sample.inputs).gauge
    expect(statistical).toMatchObject({ rateLabel: 'Gesamtfehlerquote', upperLabel: 'obere Fehlergrenze' })
    expect(nbsp(statistical?.description ?? '')).toBe('Gesamtfehlerquote 0,65 %, obere Fehlergrenze 1,09 %, Wesentlichkeitsschwelle 2,00 %')
    for (const id of ['13_NS_GW', '14_NS_GW_S', '15_NS_PPS', '16_NS_PPS_S']) {
      const gauge = summaryOf(sheetOf(id), sheetOf(id).sample.inputs).gauge
      expect(gauge, id).toMatchObject({ rateLabel: 'Gesamtfehlerquote', upperLabel: null, upper: null })
      expect(gauge?.description, id).not.toContain('obere Fehlergrenze')
    }
    for (const id of ['X1_KonsMUS_2017', 'X2_DiffSch_2017', 'X3_DiffSch_S_2017', 'X4_DiffSch_2Z_2017']) {
      const gauge = summaryOf(sheetOf(id), sheetOf(id).sample.inputs).gauge
      expect(gauge?.rateLabel, id).toBe('Projected error rate')
      expect(gauge?.upperLabel, id).toMatch(/^Upper limit of/)
    }
  })
})

describe('Fehlende Angaben in geschichteten Blättern', () => {
  it('genannt werden die Eingaben belegter Schichten, nicht die aller zwanzig Spalten', () => {
    const sheet = sheetOf('04_MUS_1Z_S')
    const evaluation = evaluateSheet(sheet, { ...sheet.sample.inputs, E24: null }, context)
    expect(evaluation.cells.C27).toBeNull()
    expect(evaluation.lacking.get('C27')).toEqual(['E24'])
    expect(summaryOf(sheet, { ...sheet.sample.inputs, E24: null }).primaryNote).toContain('(E24)')
  })
})

describe('Schichtspalten je Blatt (Altvorlage X3: E–K)', () => {
  const sheet = sheetOf('X3_DiffSch_S_2017')
  const columns = strataColumnsOf(sheet.definition)

  it('die Schichtspalten kommen aus der Definition', () => {
    expect(columns.slice(0, 7)).toEqual(['E', 'F', 'G', 'H', 'I', 'J', 'K'])
    expect(columns).toHaveLength(20)
    expect(strataColumnsOf(sheetOf('04_MUS_1Z_S').definition).slice(0, 7)).toEqual(['D', 'E', 'F', 'G', 'H', 'I', 'J'])
    expect(strataColumnsOf(sheetOf('03_MUS_1Z').definition)).toEqual([])
  })

  it('belegte Schichten zählen in den Spalten des Blatts: K ist die siebte, nicht die achte', () => {
    const rows = strataRows(sheet)
    expect(usedStrata({ E6: 1, F6: 2, G6: 3 }, rows, columns)).toBe(3)
    expect(usedStrata({ K6: 300 }, rows, columns)).toBe(7)
    expect(usedStrata({ AA6: 300 }, rows, columns)).toBe(8)
    // Mit den Spalten D–J gezählt (der frühere Fehler) wäre K unsichtbar und G die vierte Schicht.
    expect(usedStrata({ K6: 300 }, rows)).toBe(0)
  })

  it('Export und Import: die siebte Schicht in Spalte K bleibt sichtbar', async () => {
    const inputs = { ...sheet.sample.inputs, K6: 900000, K7: 40, K8: 300 }
    const state = { ...emptyWorkspace(), activeMethod: sheet.id, sheets: { [sheet.id]: inputs } }
    const exported = await exportWorkbook(state)
    const cells = readWorkbook(exported.data).cells('Ergebnis')
    const texts = [...cells.values()].map((cell) => cell.value)
    expect(texts).toContain('Schicht 7')
    expect(texts).not.toContain('Schicht 8')
    expect(texts).toContain(900000)
    const reopened = importWorkbook(exported.data)
    expect(reopened.kind).toBe('workspace')
  })
})

describe('Datentabelle (Blatt X1a)', () => {
  it('X1a ist kein Rechenblatt, sondern eine Nachschlagetabelle, die zu X1 gehört', () => {
    expect(findAvailableSheet('X1a_RF_2017')).toBeUndefined()
    expect(sheetOf('X1_KonsMUS_2017').definition.tables).toEqual(['X1a_RF_2017'])
    expect(tableOf('X1a_RF_2017')?.title).toBe('Zuverlässigkeitsfaktoren')
    expect(tableOf('03_MUS_1Z')).toBeUndefined()
    expect(SHEETS.filter((entry) => !entry.available).map((entry) => [entry.id, Boolean(entry.table)])).toEqual([['X1a_RF_2017', true]])
  })

  it('Anzeigemodell: Gruppenüberschrift, Spalten, 51 Zeilen mit zwei Nachkommastellen', () => {
    const table = tableOf('X1a_RF_2017')
    if (!table) throw new Error('Tabelle fehlt')
    const view = buildDataTable(table)
    expect(view.groups).toEqual([{ label: '', span: 1 }, { label: 'Risk of incorrect acceptation', span: 10 }])
    expect(view.columns).toHaveLength(11)
    expect(view.columns[0]?.label).toBe('Number of errors')
    expect(view.rows).toHaveLength(51)
    // Null Fehler: 3,00 bei 5 % Risiko, 2,30 bei 10 %, 1,20 bei 30 % – Blatt X1 rechnet dagegen fest mit 2,31 und 1,21.
    expect([view.rows[0]?.[0], view.rows[0]?.[2], view.rows[0]?.[3], view.rows[0]?.[7]]).toEqual(['0', '3,00', '2,30', '1,20'])
    expect(view.rows.every((row) => row.slice(1).every((value) => /^\d+,\d{2}$/.test(value)))).toBe(true)
    expect(view.notes[0]).toContain('Altvorlage 2014–2020')
  })
})
