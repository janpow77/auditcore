/**
 * Import der ausgefüllten Vorlage: Die Gegenprobe erfasst alle Blätter und beide
 * Richtungen, und nichts an der Mappe bleibt ungenannt (Auflage V6 der
 * Gesamtabnahme): Blatt 18 ohne eigene Eingaben, kein gewähltes Methodenblatt,
 * Daten in einer achten Schichtspalte, abgeschnittene Blätter, gelöschte
 * Vorgaben, Datumswerte als Tageszahl und Kopien des Blatts 17 unter freiem Namen.
 */
import { strToU8, zipSync } from 'fflate'
import { describe, expect, it } from 'vitest'
import { sheet as sheet03 } from '../src/sheets/03_MUS_1Z/index'
import { sheet as sheet09 } from '../src/sheets/09_SRS_1Z_S/index'
import { computeWorkspace } from '../src/workspace/compute'
import { emptyWorkspace, type WorkspaceState } from '../src/workspace/types'
import { WorkbookError, compareWithWorkbook, importWorkbook } from '../src/xlsx/index'
import type { CellMap } from '../src/model/types'

type Template = Extract<ReturnType<typeof importWorkbook>, { kind: 'template' }>

const text = (cell: string, value: string): string => `<c r="${cell}" t="inlineStr"><is><t>${value}</t></is></c>`
const number = (cell: string, value: number): string => `<c r="${cell}"><v>${value}</v></c>`
const cellsOf = (values: CellMap): string => Object.entries(values).map(([cell, value]) => (typeof value === 'number' ? number(cell, value) : value === null ? '' : text(cell, String(value)))).join('')
const sheetXml = (values: CellMap): string => `<worksheet><sheetData><row r="1">${cellsOf(values)}</row></sheetData></worksheet>`

/** Arbeitsmappe aus rohem XML mit mehreren Blättern. */
function workbookOf(sheets: Record<string, string>): Uint8Array {
  const names = Object.keys(sheets)
  return zipSync({
    'xl/workbook.xml': strToU8(`<workbook><sheets>${names.map((name, index) => `<sheet name="${name}" sheetId="${index + 1}" r:id="rId${index + 1}"/>`).join('')}</sheets></workbook>`),
    'xl/_rels/workbook.xml.rels': strToU8(`<Relationships>${names.map((_, index) => `<Relationship Id="rId${index + 1}" Target="worksheets/sheet${index + 1}.xml"/>`).join('')}</Relationships>`),
    ...Object.fromEntries(names.map((name, index) => [`xl/worksheets/sheet${index + 1}.xml`, strToU8(sheets[name] ?? '')])),
  })
}

function template(sheets: Record<string, string>): Template {
  const imported = importWorkbook(workbookOf(sheets))
  if (imported.kind !== 'template') throw new Error('keine Vorlage')
  return imported
}

const state = (imported: Template, activeMethod: string | null): WorkspaceState => ({ ...emptyWorkspace(), activeMethod, sheets: Object.fromEntries(imported.filled.map((id) => [id, imported.sheets[id] ?? {}])) })
/** Rechenwerte, wie die Webfassung sie für die Eingaben zeigt – als hätte die Mappe sie berechnet. */
const computedBy = (inputs: CellMap, id: string): CellMap => computeWorkspace({ ...emptyWorkspace(), activeMethod: id, sheets: { [id]: inputs } })[id] ?? {}
const formulas = (sheet: typeof sheet03, values: CellMap): CellMap => Object.fromEntries(Object.entries(values).filter(([cell]) => !(cell in sheet.sample.inputs)))

describe('Gegenprobe beim Import: alle Blätter, beide Richtungen', () => {
  const results03 = formulas(sheet03, computedBy(sheet03.sample.inputs, '03_MUS_1Z'))

  it('Blatt 18 gilt als ausgefüllt, sobald dort das Methodenblatt gewählt ist, und wird verglichen', () => {
    const imported = template({ '03_MUS_1Z': sheetXml({ ...sheet03.sample.inputs, ...results03 }), '18_GFQ_AnhIII': sheetXml({ C4: '03_MUS_1Z', C29: 0.02, C20: 'Nein', C26: 0.5 }) })
    expect(imported.filled).toEqual(['03_MUS_1Z', '18_GFQ_AnhIII'])
    expect(imported.method).toBe('03_MUS_1Z')
    const differences = compareWithWorkbook(state(imported, imported.method), imported.cached)
    expect(differences.filter((entry) => entry.sheet === '03_MUS_1Z')).toEqual([])
    // Die Mappe trägt in Blatt 18 eine andere Gesamtfehlerquote als die Webfassung: Das wird jetzt gemeldet.
    expect(differences.find((entry) => entry.sheet === '18_GFQ_AnhIII' && entry.cell === 'C26')).toMatchObject({ workbook: 0.5, kind: expect.stringMatching(/^(value|webOpen)$/) })
  })

  it('Mappe leer, Webfassung mit Wert – und umgekehrt – wird gemeldet; „Angabe fehlt“ ist als begründet gekennzeichnet', () => {
    const { C42: _projected, ...withoutProjected } = results03
    // C42 trägt in der Mappe eine Formel ohne Ergebnis; eine Zelle, die es in der Mappe gar nicht gibt, wird nicht verglichen.
    const emptyFormula = `<row r="2"><c r="C42"><f>IFERROR(1/0,"")</f><v></v></c><c r="C12"><f>1+0</f><v>${String(results03.C12)}</v></c></row>`
    const imported = template({ '03_MUS_1Z': sheetXml({ ...sheet03.sample.inputs, ...withoutProjected }).replace('</sheetData>', `${emptyFormula}</sheetData>`) })
    const empty = compareWithWorkbook(state(imported, '03_MUS_1Z'), imported.cached)
    expect(empty).toEqual([expect.objectContaining({ cell: 'C42', workbook: null, kind: 'workbookEmpty', explained: false })])
    expect(typeof empty[0]?.computed).toBe('number')
    // Ohne voraussichtliche Fehlerquote rechnet die Vorlage mit 0 weiter; die Webfassung zeigt „Angabe fehlt“.
    const lacking = template({ '03_MUS_1Z': sheetXml({ ...sheet03.sample.inputs, C17: null, ...results03 }) })
    const open = compareWithWorkbook(state(lacking, '03_MUS_1Z'), lacking.cached).filter((entry) => entry.cell === 'C27')
    expect(open).toEqual([expect.objectContaining({ computed: null, kind: 'webOpen', explained: true })])
  })

  it('Ergebnisübersicht N3–N11 der Verfahrensblätter wird mitverglichen', () => {
    const imported = template({ '03_MUS_1Z': sheetXml({ ...sheet03.sample.inputs, ...results03, N11: 0.9 }) })
    expect(compareWithWorkbook(state(imported, '03_MUS_1Z'), imported.cached)).toEqual([expect.objectContaining({ cell: 'N11', workbook: 0.9, kind: 'value' })])
  })

  it('kein Methodenblatt in Blatt 18 gewählt: Hinweis, und Blatt 18 zeigt in der Webfassung Werte, wo die Mappe leer ist', () => {
    const imported = template({ '03_MUS_1Z': sheetXml({ ...sheet03.sample.inputs, ...results03 }), '18_GFQ_AnhIII': sheetXml({ C29: 0.02, C20: 'Nein' }) })
    expect(imported.method).toBeNull()
    expect(imported.filled).toEqual(['03_MUS_1Z'])
    expect(imported.notes).toEqual([{ kind: 'method-not-chosen', sheet: '18_GFQ_AnhIII', detail: 'C4' }])
  })
})

describe('Import: nichts an der Mappe bleibt ungenannt', () => {
  it('achte Schichtspalte K: Zahlen außerhalb der gelesenen Schichtspalten werden genannt, Fundstellen (Text) nicht', () => {
    const imported = template({ '09_SRS_1Z_S': sheetXml({ ...sheet09.sample.inputs, K12: 77, K13: 5000000, K45: 'Fundstelle der Vorlage', L13: 1 }) })
    expect(imported.notes).toEqual([{ kind: 'unread-cells', sheet: '09_SRS_1Z_S', detail: 'K12, K13, L13' }])
    expect(imported.sheets['09_SRS_1Z_S']).not.toHaveProperty('K12')
  })

  it('abgeschnittenes Blatt: Lesefehler statt eines teilweise gelesenen Blatts', () => {
    const cut = sheetXml(sheet03.sample.inputs).slice(0, -40)
    expect(() => importWorkbook(workbookOf({ '03_MUS_1Z': cut }))).toThrow(WorkbookError)
    expect(() => importWorkbook(workbookOf({ '03_MUS_1Z': cut }))).toThrow(/unvollständig/)
  })

  it('gelöschte Vorgabe in einem ausgefüllten Blatt: als leere Zelle übernommen und genannt', () => {
    const { C14: _materiality, ...withoutDefault } = sheet03.sample.inputs
    const imported = template({ '03_MUS_1Z': sheetXml(withoutDefault) })
    expect(imported.sheets['03_MUS_1Z']).toMatchObject({ C14: null })
    expect(imported.notes).toEqual([{ kind: 'default-cleared', sheet: '03_MUS_1Z', detail: 'C14' }])
    // Die Webfassung rechnet wie die Mappe ohne Wesentlichkeitsschwelle, statt 2 % wieder einzusetzen.
    expect(computeWorkspace(state(imported, '03_MUS_1Z'))['03_MUS_1Z']).toMatchObject({ C14: null, C16: null })
    // Ein Blatt, das nur Vorgaben trug, wird durch fehlende Vorgaben nicht zum ausgefüllten Blatt.
    expect(template({ '03_MUS_1Z': sheetXml({ C11: 'zweiseitig' }) }).filled).toEqual([])
  })

  it('Datum als Tageszahl: als Datum übernommen und genannt', () => {
    const imported = template({ '20_Druck_KOM': sheetXml({ J4: 46308, J5: 'endgültig' }) })
    expect(imported.sheets['20_Druck_KOM']).toMatchObject({ J4: '13.10.2026' })
    expect(imported.issues).toContainEqual(expect.objectContaining({ cell: 'J4', found: '46308', reason: 'date-from-serial', used: '13.10.2026' }))
  })

  it('Kopie des Blatts 17 unter freiem Namen: am Titel erkannt, gelesen und genannt', () => {
    const unit = { A1: '17  Unterstichprobe', C5: 'Vorhaben A', C6: 250000, C7: 140, C10: 30, C11: 61000, C12: 915 }
    const imported = template({ '17_Unterstichprobe': sheetXml(unit), 'Vorhaben B': sheetXml({ ...unit, C5: 'Vorhaben B', C6: 180000 }), Notizen: sheetXml({ A1: 'etwas anderes', C6: 1 }) })
    expect((imported.sheets['17_Unterstichprobe'] as readonly CellMap[]).map((row) => row.C5)).toEqual(['Vorhaben A', 'Vorhaben B'])
    expect(imported.notes).toEqual([{ kind: 'list-copy', sheet: '17_Unterstichprobe', detail: 'Vorhaben B' }])
  })
})
