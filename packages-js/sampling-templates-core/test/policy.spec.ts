import { describe, expect, it } from 'vitest'
import { evaluateSheet } from '../src/model/evaluate'
import { MISSING_POLICY, STRICT_POLICY, TEMPLATE_POLICY, policyOf, unfounded } from '../src/model/policy'
import { createContext } from '../src/model/sheet'
import { findAvailableSheet } from '../src/sheets/registry'
import { loadGolden, selectedSheets, templateMismatches } from './golden'

/**
 * Die Richtlinie für fehlende Angaben (`src/model/policy.ts`) ist die eine Stelle,
 * an der sich das Verhalten aller Blätter umstellen lässt. Geprüft werden beide
 * Varianten: die geltende im Golden-Abgleich (`golden.spec.ts`), die Variante
 * „wie die Vorlage“ hier – sie muss in jeder Zelle jedes Falls den Wert der Vorlage zeigen.
 */
describe('Richtlinie für fehlende Angaben', () => {
  it('geltende Richtlinie: Pflichteingaben offen, Standardabweichung der Stichprobe und Teilfehlersummen mit 0, Prüfhinweise ohne Grundlage offen', () => {
    expect(MISSING_POLICY).toEqual({ requiredInput: 'missing', sampleDeviation: 'zero', partialErrorSum: 'zero', withoutBasis: 'open' })
    expect(policyOf(undefined)).toBe(MISSING_POLICY)
    expect(unfounded(undefined, '✔ ≥ 3')).toBeNull()
    expect(unfounded({ policy: TEMPLATE_POLICY }, '✔ ≥ 3')).toBe('✔ ≥ 3')
  })

  for (const sheet of selectedSheets()) {
    it(`${sheet.id}: Variante „wie die Vorlage“ zeigt in jedem Fall genau die Werte der Vorlage`, () => {
      const mismatches = loadGolden(sheet.id).flatMap((golden) => templateMismatches(sheet, golden).map((entry) => `${golden.name}: ${entry.cell}`))
      expect(mismatches).toEqual([])
    })
  }

  it('Blatt 03 ohne s_r: geltend mit 0 gerechnet und ausgewiesen, streng offen mit Nennung der Eingabe, wie die Vorlage ebenfalls ausgewiesen', () => {
    const sheet = findAvailableSheet('03_MUS_1Z')
    if (!sheet) throw new Error('Blatt 03 fehlt')
    const inputs = { ...sheet.sample.inputs, C39: null }
    const current = evaluateSheet(sheet, inputs, createContext())
    expect(current.cells.C43).toBe(0)
    expect(current.assumed).toEqual([{ input: 'C39', cells: ['C43', 'C46', 'C47', 'C48', 'C51', 'C52'] }])
    const strict = evaluateSheet(sheet, inputs, createContext({ policy: STRICT_POLICY }))
    expect(strict.cells.C43).toBeNull()
    expect(strict.cells.C52).toBeNull()
    expect(strict.assumed).toEqual([])
    expect(strict.lacking.get('C43')).toEqual(['C39'])
    expect(evaluateSheet(sheet, inputs, createContext({ policy: TEMPLATE_POLICY })).assumed).toEqual(current.assumed)
  })

  it('Blatt 03 ohne voraussichtliche Standardabweichung: geltend „Angabe fehlt“ mit Eingabe, wie die Vorlage mit 0 gerechnet und ausgewiesen', () => {
    const sheet = findAvailableSheet('03_MUS_1Z')
    if (!sheet) throw new Error('Blatt 03 fehlt')
    const inputs = { ...sheet.sample.inputs, C20: null }
    const current = evaluateSheet(sheet, inputs, createContext())
    expect(current.cells.C27).toBeNull()
    expect(current.lacking.get('C27')).toEqual(['C20'])
    const template = evaluateSheet(sheet, inputs, createContext({ policy: TEMPLATE_POLICY }))
    expect(template.cells.C27).toBe(30)
    expect(template.lacking.size).toBe(0)
    expect(template.assumed.find((entry) => entry.input === 'C20')?.cells).toContain('C27')
  })
})
