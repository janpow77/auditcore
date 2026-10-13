import { describe, expect, it } from 'vitest'
import { defaultInputs } from '../src/model/definition'
import { evaluateSheet } from '../src/model/evaluate'
import { createContext, type AvailableSheet } from '../src/model/sheet'
import type { CellMap, Deviation } from '../src/model/types'
import { contextFor } from '../src/workspace/compute'
import { caseState, caseWorkspace, compareCase, loadGolden, selectedSheets, type GoldenCase } from './golden'

/**
 * Zellen, die der Fall bei vollständigen Pflichteingaben wie die Vorlage zeigt,
 * obwohl die Grundlage fehlt (Fallart `withoutBasis`): Der Golden-Abgleich hat
 * dort den Wert der Vorlage bestätigt, die Webfassung kennzeichnet ihn.
 */
function shownWithoutBasis(sheet: AvailableSheet, golden: GoldenCase): readonly string[] {
  if (sheet.definition.layout === 'list') return evaluateSheet(sheet, { ...defaultInputs(sheet.definition), ...(golden.eingaben as CellMap) }, createContext(), false).withoutBasis
  const state = caseState(sheet, golden)
  return evaluateSheet(sheet, (state.sheets[sheet.id] ?? {}) as CellMap, contextFor(sheet.id, state, caseWorkspace(sheet, golden)), false).withoutBasis
}

describe('Begründete Abweichungen', () => {
  for (const sheet of selectedSheets()) {
    it(`${sheet.id}: jede erklärte Abweichung ist durch einen Golden-Fall belegt`, () => {
      // Schichtzeilen: Die Vorlage hat sieben Schichtspalten, die Webfassung bis zu zwanzig. Eine Zeile gilt als
      // belegt, wenn dieselbe Abweichung (Zeile, Anzeige der Vorlage, Begründung) in einer Schichtspalte belegt ist.
      const pattern = (deviation: Deviation): string => [deviation.cell.replace(/^[A-Z]+/, ''), deviation.cell.startsWith('N') ? 'N' : '', deviation.template, deviation.reason, deviation.kind ?? ''].join('|')
      const cases = loadGolden(sheet.id)
      const used = new Set(cases.flatMap((golden) => compareCase(sheet, golden).explained.map((entry) => pattern(entry.deviation))))
      // Werte ohne Grundlage sind auch belegt, wenn ein Fall sie bei vollständigen Pflichteingaben wie die Vorlage zeigt.
      const shown = new Set(cases.flatMap((golden) => shownWithoutBasis(sheet, golden)))
      for (const deviation of sheet.deviations) if (deviation.kind === 'withoutBasis' && shown.has(deviation.cell)) used.add(pattern(deviation))
      const unused = sheet.deviations.filter((deviation) => !used.has(pattern(deviation))).map((deviation) => deviation.cell)
      expect(unused).toEqual([])
    }, 240_000)

    it(`${sheet.id}: Abweichungen betreffen nur Formelzellen des Blatts`, () => {
      const results = sheet.compute({}, createContext())
      for (const deviation of sheet.deviations) expect(Object.keys(results)).toContain(deviation.cell)
    })
  }
})
