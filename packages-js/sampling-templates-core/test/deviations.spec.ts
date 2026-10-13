import { describe, expect, it } from 'vitest'
import { createContext } from '../src/model/sheet'
import type { Deviation } from '../src/model/types'
import { compareCase, loadGolden, selectedSheets } from './golden'

describe('Begründete Abweichungen', () => {
  for (const sheet of selectedSheets()) {
    it(`${sheet.id}: jede erklärte Abweichung ist durch einen Golden-Fall belegt`, () => {
      // Schichtzeilen: Die Vorlage hat sieben Schichtspalten, die Webfassung bis zu zwanzig. Eine Zeile gilt als
      // belegt, wenn dieselbe Abweichung (Zeile, Anzeige der Vorlage, Begründung) in einer Schichtspalte belegt ist.
      const pattern = (deviation: Deviation): string => [deviation.cell.replace(/^[A-Z]+/, ''), deviation.cell.startsWith('N') ? 'N' : '', deviation.template, deviation.reason, deviation.kind ?? ''].join('|')
      const used = new Set(loadGolden(sheet.id).flatMap((golden) => compareCase(sheet, golden).explained.map((entry) => pattern(entry.deviation))))
      const unused = sheet.deviations.filter((deviation) => !used.has(pattern(deviation))).map((deviation) => deviation.cell)
      expect(unused).toEqual([])
    })

    it(`${sheet.id}: Abweichungen betreffen nur Formelzellen des Blatts`, () => {
      const results = sheet.compute({}, createContext())
      for (const deviation of sheet.deviations) expect(Object.keys(results)).toContain(deviation.cell)
    })
  }
})
