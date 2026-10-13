/**
 * Arbeitshilfe beim Nachbauen eines Blatts: schreibt die unbegründeten
 * Abweichungen je Fall kompakt in eine Datei.
 *
 *   SAMPLING_TEMPLATES_REPORT=/tmp/abweichungen.txt npx vitest run test/report.spec.ts
 *   SAMPLING_TEMPLATES_REPORT=… SAMPLING_TEMPLATES_SHEET=04_MUS_1Z_S npx vitest run test/report.spec.ts
 */
import { writeFileSync } from 'node:fs'
import { describe, it } from 'vitest'
import { availableSheets } from '../src/sheets/registry'
import { compareCase, loadGolden } from './golden'

const target = process.env.SAMPLING_TEMPLATES_REPORT ?? ''
const only = process.env.SAMPLING_TEMPLATES_SHEET ?? ''

describe.skipIf(!target)('Abweichungsbericht (Arbeitshilfe)', () => {
  it('schreibt die unbegründeten Abweichungen je Fall', () => {
    const lines: string[] = []
    for (const sheet of availableSheets().filter((entry) => !only || entry.id === only)) {
      for (const golden of loadGolden(sheet.id)) {
        const report = compareCase(sheet, golden)
        if (report.unexplained.length === 0) continue
        const cells = report.unexplained.map((entry) => `${entry.cell}: Vorlage ${JSON.stringify(entry.expected)} / Web ${JSON.stringify(entry.actual)}`)
        lines.push(`${sheet.id} – ${golden.name}`, ...cells.map((cell) => `    ${cell}`))
      }
    }
    writeFileSync(target, `${lines.join('\n')}\n`)
  })
})
