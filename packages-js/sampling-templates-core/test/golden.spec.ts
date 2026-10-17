import { describe, expect, it } from 'vitest'
import { compareCase, loadGolden, selectedSheets } from './golden'

describe('Golden-Abgleich mit der Vorlage (LibreOffice-Neuberechnung)', () => {
  for (const sheet of selectedSheets()) {
    const cases = loadGolden(sheet.id)
    it(`${sheet.id}: mindestens 12 Fälle`, () => expect(cases.length).toBeGreaterThanOrEqual(12))
    for (const golden of cases) {
      it(`${sheet.id}: ${golden.name}`, () => {
        const report = compareCase(sheet, golden)
        expect(report.unexplained).toEqual([])
      })
    }
  }
})
