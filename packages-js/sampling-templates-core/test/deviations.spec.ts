import { describe, expect, it } from 'vitest'
import { createContext } from '../src/model/sheet'
import { availableSheets } from '../src/sheets/registry'
import { compareCase, loadGolden } from './golden'

/** `SAMPLING_TEMPLATES_SHEET=<Blatt>` beschränkt den Lauf auf ein Blatt. */
const ONLY = process.env.SAMPLING_TEMPLATES_SHEET ?? ''

describe('Begründete Abweichungen', () => {
  for (const sheet of availableSheets().filter((entry) => !ONLY || entry.id === ONLY)) {
    it(`${sheet.id}: jede erklärte Abweichung ist durch einen Golden-Fall belegt`, () => {
      const used = new Set(loadGolden(sheet.id).flatMap((golden) => compareCase(sheet, golden).explained.map((entry) => entry.deviation)))
      const unused = sheet.deviations.filter((deviation) => !used.has(deviation)).map((deviation) => deviation.cell)
      expect(unused).toEqual([])
    })

    it(`${sheet.id}: Abweichungen betreffen nur Formelzellen des Blatts`, () => {
      const results = sheet.compute({}, createContext())
      for (const deviation of sheet.deviations) expect(Object.keys(results)).toContain(deviation.cell)
    })
  }
})
