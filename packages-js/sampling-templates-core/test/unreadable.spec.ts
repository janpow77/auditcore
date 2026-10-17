import { describe, expect, it } from 'vitest'
import { createTranslate } from '../src/i18n/messages'
import { cellsOf, inputFields } from '../src/model/definition'
import { dependentCells } from '../src/model/dependence'
import { evaluateSheet } from '../src/model/evaluate'
import { UNREADABLE_INPUT, type AvailableSheet } from '../src/model/sheet'
import type { CellMap } from '../src/model/types'
import { availableSheets, findAvailableSheet } from '../src/sheets/registry'
import { buildSections } from '../src/view/sheetView'
import { buildSummary } from '../src/view/summaryView'
import { computeWorkspace, contextFor } from '../src/workspace/compute'
import { emptyWorkspace, type WorkspaceState } from '../src/workspace/types'

/**
 * Ungültige Eingaben (Text, den die Oberfläche nicht als Zahl lesen kann:
 * „abc“, zu viele Nachkommastellen, mehrdeutiger Trenner) kommen als
 * `UNREADABLE_INPUT` in die Rechnung. Sie dürfen nie wie ein leeres Feld
 * weiterrechnen – weder mit 0 (Standardabweichungen der Stichprobe) noch mit
 * der Vorbelegung noch als „keine“ (freiwillige Felder).
 */
const t = createTranslate()

/** Arbeitsstand mit den Beispielwerten aller Formularblätter, aktives Verfahren `method`. */
function sampleState(method: string): WorkspaceState {
  const sheets: Record<string, CellMap> = {}
  for (const sheet of availableSheets()) if (sheet.definition.layout !== 'list') sheets[sheet.id] = { ...sheet.sample.inputs }
  return { ...emptyWorkspace(), activeMethod: method, sheets }
}

const contextOf = (sheet: AvailableSheet, state: WorkspaceState) => contextFor(sheet.id, state, computeWorkspace(state))

describe('Ungültige Eingaben', () => {
  it('Eigenschaft: Für jedes Zahlenfeld jedes Blatts liefert „ungültig“ nie das Ergebnis von „leer“, wo das leere Feld zu einem Wert führt', () => {
    let checked = 0
    for (const sheet of availableSheets().filter((entry) => entry.definition.layout !== 'list' && entry.id !== '01_Parameter')) {
      const state = sampleState(['18_GFQ_AnhIII', '20_Druck_KOM'].includes(sheet.id) ? '08_SRS_1Z' : (sheet.id.startsWith('0') || sheet.id.startsWith('1') ? sheet.id : '03_MUS_1Z'))
      const context = contextOf(sheet, state)
      const sample = (state.sheets[sheet.id] as CellMap | undefined) ?? {}
      const cells = inputFields(sheet.definition).filter((field) => field.type !== 'text' && !field.options && !field.list).flatMap((field) => cellsOf(field).filter((cell) => !field.columns || cell in sample || cellsOf(field)[0] === cell))
      for (const cell of cells) {
        const blankInputs = { ...sample, [cell]: null }
        const blankBase = sheet.compute(blankInputs, context)
        const blank = evaluateSheet(sheet, blankInputs, context, false).cells
        const dependents = dependentCells(sheet, blankInputs, cell, blankBase, context).filter((target) => blank[target] !== null && blank[target] !== undefined)
        if (dependents.length === 0) continue
        const invalid = evaluateSheet(sheet, { ...sample, [cell]: UNREADABLE_INPUT }, context)
        expect(dependents.map((target) => [target, invalid.cells[target] ?? null]), `${sheet.id} ${cell}`).toEqual(dependents.map((target) => [target, null]))
        expect(dependents.every((target) => invalid.lacking.get(target)?.includes(cell)), `${sheet.id} ${cell}`).toBe(true)
        expect(invalid.assumed.map((entry) => entry.input), `${sheet.id} ${cell}`).not.toContain(cell)
        checked += 1
      }
    }
    expect(checked).toBeGreaterThan(300)
  }, 600_000)

  it('Blatt 08, s_q ungültig: keine Genauigkeit 0 €, keine grüne Würdigung, „Eingabe ungültig“ – leer dagegen „mit 0 berechnet“', () => {
    const sheet = findAvailableSheet('08_SRS_1Z')!
    const state = sampleState(sheet.id)
    const context = contextOf(sheet, state)
    const invalidInputs = { ...sheet.sample.inputs, C39: UNREADABLE_INPUT }
    const invalid = evaluateSheet(sheet, invalidInputs, context)
    expect([invalid.cells.C44, invalid.cells.C52, invalid.cells.C53, invalid.cells.N7]).toEqual([null, null, null, null])
    const summary = buildSummary(sheet, invalidInputs, invalid.cells, context, t, new Set(['C39']))
    expect(summary.hints.map((hint) => hint.text).join(' ')).not.toContain('unter der Signifikanzschwelle')
    // Ergebnisspalte: offene Kennzahlen „Eingabe ungültig“ mit Nennung der Eingabe; die Gesamtfehlerquote hängt nicht an s_q und bleibt.
    const rows = Object.fromEntries(summary.rows.map((row) => [row.label, row.value]))
    expect(Object.values(rows)).toContain('Eingabe ungültig')
    expect(Object.entries(rows).find(([label]) => label.startsWith('Gesamtfehlerquote'))?.[1]).toMatch(/%$/)
    expect(summary.invalidNote).toMatch(/^Eingabe ungültig\. Ungültige Eingabe: .*\(s_q\) \(C39\)$/)
    expect(summary.gauge).toBeNull()
    expect(buildSummary(sheet, sheet.sample.inputs, sheet.compute(sheet.sample.inputs, context), context, t).invalidNote).toBe('')
    const formRows = buildSections(sheet, invalidInputs, invalid.cells, context, t, new Set(['C39'])).flatMap((section) => section.rows ?? [])
    expect(JSON.stringify(formRows.filter((row) => ['C44', 'C52', 'C53'].includes(row.cell)))).toContain('Eingabe ungültig')
    // Wirklich leer: mit 0 gerechnet und ausgewiesen.
    const empty = evaluateSheet(sheet, { ...sheet.sample.inputs, C39: null }, context)
    expect(empty.cells.C44).toBe(0)
    expect(empty.assumed.map((entry) => entry.input)).toContain('C39')
    const emptyRows = buildSections(sheet, { ...sheet.sample.inputs, C39: null }, empty.cells, context, t, new Set()).flatMap((section) => section.rows ?? [])
    expect(JSON.stringify(emptyRows.filter((row) => row.cell === 'C44'))).toContain('Keine Angabe, daher mit 0 berechnet')
  })
})
