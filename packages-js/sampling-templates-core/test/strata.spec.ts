import { describe, expect, it } from 'vitest'
import { createTranslate } from '../src/i18n/messages'
import { cellsOf, findField, inputCells } from '../src/model/definition'
import { createContext } from '../src/model/sheet'
import { EXTRA_STRATA, MAX_STRATA, STRATA_COLUMNS, TEMPLATE_STRATA, countRow, fillRow, rowValues, stratumCell, sumRow, usedStrata } from '../src/model/strata'
import type { CellValue } from '../src/model/types'
import { sheet } from '../src/sheets/04_MUS_1Z_S/index'
import { buildSections, strataRows } from '../src/view/sheetView'
import { buildSummary } from '../src/view/summaryView'
import { openWorkspace } from '../src/workspace/open'
import { saveWorkspace } from '../src/workspace/save'
import { emptyWorkspace, type WorkspaceState } from '../src/workspace/types'
import { exportWorkbook, importWorkbook, readWorkbook, writeWorkbook } from '../src/xlsx/index'

const context = createContext()
const t = createTranslate()
const nbsp = (text: string): string => text.replaceAll(String.fromCharCode(160), ' ')

/** Beispielwerte mit einer achten Schicht (Spalte AA der Webfassung). */
const eight: Record<string, CellValue> = { ...sheet.sample.inputs, G9: 1000000, H9: 1000000, I9: 1000000, J9: 1000000, AA9: 2000000, G24: 0.1, H24: 0.1, I24: 0.1, J24: 0.1, AA24: 0.2, AA46: 0.1, AA47: 0.05 }

describe('Schichtspalten', () => {
  it('sieben Spalten der Vorlage, dreizehn weitere der Webfassung', () => {
    expect(TEMPLATE_STRATA).toEqual(['D', 'E', 'F', 'G', 'H', 'I', 'J'])
    expect(EXTRA_STRATA[0]).toBe('AA')
    expect(EXTRA_STRATA.at(-1)).toBe('AM')
    expect(STRATA_COLUMNS).toHaveLength(20)
    expect(MAX_STRATA).toBe(20)
    expect(stratumCell('AA', 9)).toBe('AA9')
  })

  it('Summen, Anzahl und belegte Schichten über alle Schichtspalten', () => {
    const cells = { D9: 10, F9: 5, AA9: 1, D10: 'Text', E10: null }
    expect(sumRow(cells, 9)).toBe(16)
    expect(countRow(cells, 9)).toBe(3)
    expect(sumRow(cells, 10)).toBe(0)
    expect(rowValues(cells, 9, TEMPLATE_STRATA)).toEqual([10, null, 5, null, null, null, null])
    expect(usedStrata(cells, [9])).toBe(8)
    expect(usedStrata({ E9: 1 }, [9, 10])).toBe(2)
    expect(usedStrata({}, [9])).toBe(0)
    const filled: Record<string, CellValue> = {}
    fillRow(filled, 3, (column) => (column === 'D' ? 1 : null))
    expect(Object.keys(filled)).toHaveLength(20)
    expect(filled.D3).toBe(1)
  })

  it('Schichtzeilen der Definition lösen sich in Zellen je Spalte auf', () => {
    const field = findField(sheet.definition, 'D9')!
    expect(field.total).toBe('C9')
    expect(cellsOf(field)).toHaveLength(20)
    expect(findField(sheet.definition, 'H9')).toBe(field)
    expect(findField(sheet.definition, 'C9')).toBe(field)
    expect(findField(sheet.definition, 'AM47')?.alias).toBe('stratumSampleDeviation')
    expect(inputCells(sheet.definition)).toEqual(expect.arrayContaining(['C4', 'D9', 'J9', 'AA9', 'AM47']))
    expect(strataRows(sheet)).toEqual(['9', '10', '24', '37', '38', '43', '45', '46', '47'])
  })
})

describe('Blatt 04_MUS_1Z_S', () => {
  it('Beispielwerte mit drei Schichten', () => {
    const results = sheet.compute(sheet.sample.inputs, context)
    expect(results.C9).toBe(48500000)
    expect(results.C10).toBe(420)
    expect(results.C33).toBeGreaterThanOrEqual(30)
    expect(results.C35).toBeGreaterThanOrEqual(results.C33 as number)
    expect(results.G35).toBeNull()
    expect(results.N3).toBe('MUS-Standardansatz, 1 Zeitraum, geschichtet')
    expect(results.C63).toBe('✔ GFQ und obere Fehlergrenze unter der Schwelle')
  })

  it('die achte Schicht rechnet wie die ersten sieben und ist als Hinweis der Webfassung gekennzeichnet', () => {
    const results = sheet.compute(eight, context)
    expect(results.C9).toBe(54500000)
    expect(results.AA35).toBeGreaterThan(0)
    expect(results.AA42).toBeGreaterThan(0)
    expect(results.C35).toBe(STRATA_COLUMNS.reduce((total, column) => total + ((results[`${column}35`] as number | null) ?? 0), 0))
    expect(sheet.webHints?.(eight, results, context).map((hint) => hint.id)).toContain('strata-beyond-template')
    expect(sheet.webHints?.(sheet.sample.inputs, sheet.compute(sheet.sample.inputs, context), context).map((hint) => hint.id)).not.toContain('strata-beyond-template')
  })

  it('fehlt die Standardabweichung einer belegten Schicht, bleiben Umfang und Folgegrößen offen', () => {
    const results = sheet.compute({ ...sheet.sample.inputs, E24: null }, context)
    expect([results.E25, results.C25, results.C26, results.C27, results.C33, results.C35, results.C61]).toEqual([null, null, null, null, null, null, null])
    expect(results.C39).toBe(42300000)
  })

  it('fehlt die Standardabweichung der Stichprobe einer Schicht, ist ihr Beitrag 0 und wird ausgewiesen', () => {
    const results = sheet.compute({ ...sheet.sample.inputs, E47: null }, context)
    expect(results.E52).toBe(0)
    expect(sheet.zeroAssumed?.(results)).toEqual([{ input: 'E47', cells: ['E52', 'C52', 'C54', 'C57', 'C58', 'C59', 'C62', 'C63'] }])
    expect(sheet.zeroAssumed?.(sheet.compute(sheet.sample.inputs, context))).toEqual([])
  })

  it('Anzeigemodell: Schichtzeilen mit Summenzelle und je Schicht einer Zelle', () => {
    const rows = buildSections(sheet, sheet.sample.inputs, sheet.compute(sheet.sample.inputs, context), context, t).flatMap((section) => [...section.rows])
    const bookValue = rows.find((row) => row.cell === 'D9')!
    expect(bookValue.strata?.cells).toHaveLength(20)
    expect(bookValue.strata?.cells[1]).toMatchObject({ cell: 'E9', inputText: '16.500.000,00' })
    expect(nbsp(bookValue.strata?.total?.display ?? '')).toBe('48.500.000,00 €')
    expect(rows.find((row) => row.cell === 'D24')?.strata?.total).toBeNull()
    expect(rows.find((row) => row.cell === 'D41')?.strata?.cells[0]).toMatchObject({ tone: 'success', display: '✔ ≥ 3' })
    expect(rows.find((row) => row.cell === 'C12')?.strata).toBeNull()
  })

  it('Prüfhinweise je Schicht: ein gemeinsamer Hinweis oder die Schichten mit Befund', () => {
    const fine = buildSummary(sheet, sheet.sample.inputs, sheet.compute(sheet.sample.inputs, context), context, t)
    expect(fine.hints.map((hint) => hint.text)).toContain('Mindestens drei Einheiten je Zufallsschicht: ✔ ≥ 3')
    const inputs = { ...sheet.sample.inputs, E37: 40 }
    const short = buildSummary(sheet, inputs, sheet.compute(inputs, context), context, t)
    expect(short.hints).toContainEqual(expect.objectContaining({ id: 'E41', text: 'Schicht 2: ✖ < 3', tone: 'danger' }))
  })
})

describe('Schichten im Arbeitsstand und im Excel-Austausch', () => {
  const state: WorkspaceState = { ...emptyWorkspace(), activeMethod: sheet.id, sheets: { [sheet.id]: eight } }

  it('Arbeitsstand: Zellen der 8. bis 20. Schicht bleiben erhalten', async () => {
    const opened = await openWorkspace((await saveWorkspace(state)).text)
    expect(opened).toMatchObject({ ok: true, notices: [] })
    expect(opened.ok && opened.state.sheets[sheet.id]).toMatchObject({ AA9: 2000000, AA24: 0.2 })
  })

  it('Export: je belegter Schicht eine Spalte, Summe in der Wertspalte, Hinweis ab der achten Schicht', async () => {
    const exported = await exportWorkbook(state)
    const cells = readWorkbook(exported.data).cells('Ergebnis')
    const all = [...cells.entries()]
    const head = all.find(([, cell]) => cell.value === 'Schicht 8')?.[0] ?? ''
    expect(head.startsWith('N')).toBe(true)
    const row = all.find(([address, cell]) => address.startsWith('F') && cell.value === 'C9; D9:AA9')?.[0].slice(1)
    expect(cells.get(`C${row}`)?.value).toBe(54500000)
    expect(cells.get(`G${row}`)?.value).toBe(24000000)
    expect(cells.get(`N${row}`)?.value).toBe(2000000)
    expect(all.some(([, cell]) => String(cell.value).startsWith('Die Vorlage sieht sieben Schichten vor'))).toBe(true)
    const imported = importWorkbook(exported.data)
    const reopened = imported.kind === 'workspace' ? await openWorkspace(imported.text) : null
    expect(reopened?.ok && reopened.state).toEqual(state)
  })

  it('Import der ausgefüllten Vorlage liest die sieben Schichtspalten', () => {
    const rows = Array.from({ length: 12 }, (_, index) => (index === 8 ? [null, null, null, { value: 100 }, { value: 200 }, null, null, null, null, { value: 300 }] : []))
    const imported = importWorkbook(writeWorkbook([{ name: '04_MUS_1Z_S', rows }]))
    expect(imported).toMatchObject({ kind: 'template', filled: ['04_MUS_1Z_S'], sheets: { '04_MUS_1Z_S': { D9: 100, E9: 200, J9: 300 } } })
  })
})
