import { describe, expect, it } from 'vitest'
import { availableSheets } from '../src/sheets/registry'
import { compareCase, loadGolden } from './golden'

/** `SAMPLING_TEMPLATES_SHEET=<Blatt>` beschränkt den Lauf auf ein Blatt. */
const ONLY = process.env.SAMPLING_TEMPLATES_SHEET ?? ''

describe('Golden-Abgleich mit der Vorlage (LibreOffice-Neuberechnung)', () => {
  for (const sheet of availableSheets().filter((entry) => !ONLY || entry.id === ONLY)) {
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
