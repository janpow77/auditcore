import { existsSync } from 'node:fs'
import { createRequire } from 'node:module'
import { join } from 'node:path'
import { describe, expect, it } from 'vitest'
import { defaultInputs, fieldsOf, inputFields, named } from '../src/model/definition'
import { SUMMARY_CELLS, createContext, summaryOf } from '../src/model/sheet'
import type { CellValue } from '../src/model/types'
import { sheet } from '../src/sheets/03_MUS_1Z/index'
import { sameValue } from './golden'

const context = createContext()

describe('Blatt 03_MUS_1Z', () => {
  it('Beispielwerte ergeben die Größen des Gestaltungsprototyps', () => {
    const result = named(sheet.definition, sheet.compute(sheet.sample.inputs, context))
    expect(result.sampleSize).toBe(92)
    expect(result.samplingInterval).toBeCloseTo(480681.82, 2)
    expect(result.projectedError).toBeCloseTo(316422.73, 2)
    expect(result.precision).toBeCloseTo(210218.68, 2)
    expect(result.totalErrorRate).toBeCloseTo(0.00652, 5)
    expect(result.upperErrorLimitRate).toBeCloseTo(0.01086, 5)
    expect(result.assessment).toBe('✔ GFQ und obere Fehlergrenze unter der Schwelle')
  })

  it('jede Zelle und jeder Alias kommt genau einmal vor', () => {
    const fields = fieldsOf(sheet.definition)
    expect(new Set(fields.map((field) => field.cell)).size).toBe(fields.length)
    expect(new Set(fields.map((field) => field.alias)).size).toBe(fields.length)
    for (const field of fields) expect(field.alias).toMatch(/^[a-z][A-Za-z0-9]*$/)
  })

  it('der Rechenkern füllt jede Zelle der Definition und die Ergebnisübersicht', () => {
    const cells = Object.keys(sheet.compute(sheet.sample.inputs, context))
    for (const field of fieldsOf(sheet.definition)) expect(cells).toContain(field.cell)
    for (const cell of Object.values(SUMMARY_CELLS)) expect(cells).toContain(cell)
  })

  it('Vorgaben der Vorlage: zweiseitig, 2 %, Nein, Nein', () => {
    expect(defaultInputs(sheet.definition)).toEqual({ C11: 'zweiseitig', C14: 0.02, C23: 'Nein', C24: 'Nein' })
  })

  it('Beispielwerte belegen nur Eingabezellen', () => {
    const cells = inputFields(sheet.definition).map((field) => field.cell)
    for (const cell of Object.keys(sheet.sample.inputs)) expect(cells).toContain(cell)
  })

  it('Buchwert und Umfang kommen aus Blatt 02, solange sie nicht überschrieben sind', () => {
    const linked = createContext({ sheets: { '02_Grundgesamtheit': { C51: 1000, C52: 40 } } })
    expect(sheet.compute(defaultInputs(sheet.definition), linked)).toMatchObject({ C7: 1000, C8: 40, C16: 20 })
    expect(sheet.compute({ ...defaultInputs(sheet.definition), C7: 500 }, linked)).toMatchObject({ C7: 500, C8: 40, C16: 10 })
  })

  it('die Ergebnisübersicht für Blatt 18 liest die festen Zellen N3–N11', () => {
    const summary = summaryOf(sheet.id, sheet.compute(sheet.sample.inputs, context))
    expect(summary).toMatchObject({ sheet: '03_MUS_1Z', method: 'MUS-Standardansatz, 1 Zeitraum', bookValue: 48500000, sampleSize: 92, systemicErrors: 0 })
  })

  it('Hinweise der Webfassung verändern kein Ergebnis', () => {
    const inputs = { ...sheet.sample.inputs, C8: 50, C10: 0.95 }
    const results = sheet.compute(inputs, context)
    expect(sheet.webHints?.(inputs, results, context).map((hint) => hint.id)).toEqual(['size-exceeds-population', 'confidence-outside-annex'])
    expect(sheet.webHints?.(sheet.sample.inputs, sheet.compute(sheet.sample.inputs, context), context)).toEqual([])
  })
})

/**
 * Nur lokal: Abgleich mit dem Referenz-Rechenkern `engine.js` aus dem Materialordner
 * (nicht im Repository). `AUDITCORE_SAMPLING_ENGINE03=/pfad/engine.js npm test`.
 */
const enginePath = process.env.AUDITCORE_SAMPLING_ENGINE03 ?? ''
describe.skipIf(!enginePath || !existsSync(enginePath))('Blatt 03: Parität mit dem Referenz-Rechenkern (lokal)', () => {
  it('500 zufällige vollständige Belegungen stimmen überein', () => {
    const engine = createRequire(import.meta.url)(join(enginePath)) as {
      compute: (e: Record<string, CellValue>) => Record<string, CellValue>
      CELLS: Record<string, string>
      OUT: Record<string, string>
    }
    let seed = 20261013
    const random = (): number => {
      seed = (seed * 1664525 + 1013904223) % 4294967296
      return seed / 4294967296
    }
    const pick = <T,>(values: readonly T[]): T => values[Math.floor(random() * values.length)]!
    for (let run = 0; run < 500; run += 1) {
      const named: Record<string, CellValue> = {
        bv: Math.round(random() * 9e7 + 1e6), ngg: Math.round(random() * 900 + 100), zuverl: pick(['hoch', 'mittel', 'gering']), konf: pick([0.6, 0.7, 0.8, 0.9, 0.95]),
        testart: pick(['zweiseitig', 'einseitig']), wesentl: 0.02, afq: random() * 0.025, sigma: random() * 0.6 + 0.01, kategorie: pick([1, 2, 3, 4]), art83: pick(['Ja', 'Nein']),
        begrenzt: pick(['Ja', 'Nein']), ne: Math.floor(random() * 12), bve: Math.round(random() * 9e5), iter: pick([0, 0, 2]), sumEe: Math.round(random() * 5e4),
        sumRatio: random() * 2, sr: random() * 0.2, sys: pick([0, 12000]), anom: pick([0, 3400]),
      }
      const inputs: Record<string, CellValue> = {}
      for (const [name, cell] of Object.entries(engine.CELLS)) if (name in named) inputs[cell] = named[name] ?? null
      const expected = engine.compute(named)
      const actual = sheet.compute(inputs, context)
      for (const [name, cell] of Object.entries(engine.OUT)) {
        expect(sameValue(expected[name] ?? null, actual[cell] ?? null), `${cell} (${name}) Lauf ${run}`).toBe(true)
      }
    }
  })
})
