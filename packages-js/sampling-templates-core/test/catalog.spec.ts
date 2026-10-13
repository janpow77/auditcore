import { describe, expect, it } from 'vitest'
import { FAMILIES, WORKFLOW_STEPS, familyOf, findVariant } from '../src/catalog/catalog'
import { PARAMETERS, zValue } from '../src/sheets/01_Parameter/index'
import { SHEETS, availableSheets, findAvailableSheet, findSheet } from '../src/sheets/registry'
import { FormulaError } from '../src/excel/index'
import { readdirSync } from 'node:fs'
import { FOUNDATION_SHEETS } from './sheets'
import { fileURLToPath } from 'node:url'

describe('Blatt 01: Parameter', () => {
  it('z-Werte nach Anhang I Nr. 3', () => {
    expect(zValue(PARAMETERS, 0.7, 'zweiseitig')).toBe(1.036)
    expect(zValue(PARAMETERS, 0.9, 'einseitig')).toBe(1.282)
    expect(zValue(PARAMETERS, 0.95, null)).toBe(1.96)
    expect(() => zValue(PARAMETERS, 0.75, 'zweiseitig')).toThrow(FormulaError)
    expect(() => zValue(PARAMETERS, null, 'zweiseitig')).toThrow(FormulaError)
  })

  it('95 % ist als außerhalb von Anhang I gekennzeichnet', () => {
    expect(PARAMETERS.zTable.filter((row) => !row.inAnnex).map((row) => row.confidence)).toEqual([0.95])
  })
})

describe('Katalog und Register', () => {
  const variants = FAMILIES.flatMap((family) => [...family.variants])

  it('jedes Methodenblatt aus Blatt 01 steht genau einmal im Katalog', () => {
    for (const id of PARAMETERS.lists.methodSheets) expect(variants.filter((variant) => variant.sheet === id)).toHaveLength(1)
  })

  it('jede Variante und jeder Arbeitsschritt verweist auf ein Blatt des Registers', () => {
    for (const variant of variants) expect(findSheet(variant.sheet), variant.sheet).toBeDefined()
    for (const step of WORKFLOW_STEPS) if (step.sheet) expect(findSheet(step.sheet), step.sheet).toBeDefined()
  })

  it('das Register enthält jedes Blattverzeichnis außer Blatt 01', () => {
    const directories = readdirSync(fileURLToPath(new URL('../src/sheets', import.meta.url)), { withFileTypes: true })
      .filter((entry) => entry.isDirectory() && entry.name !== '01_Parameter' && entry.name !== 'shared')
      .map((entry) => entry.name)
    expect(SHEETS.map((sheet) => sheet.id).sort()).toEqual(directories.sort())
  })

  it('verfügbare Blätter tragen ihre Blattnummer in der Definition', () => {
    for (const sheet of availableSheets()) {
      expect(sheet.definition.sheet).toBe(sheet.id)
      expect(findVariant(sheet.id)?.number ?? sheet.definition.number).toBe(sheet.definition.number)
    }
    expect(findAvailableSheet('03_MUS_1Z')?.id).toBe('03_MUS_1Z')
    expect(findAvailableSheet('05_MUS_2Z', FOUNDATION_SHEETS)).toBeUndefined()
  })

  it('drei Zeiträume geschichtet ist als Lücke der Vorlage geführt', () => {
    expect(familyOf('03_MUS_1Z')?.gaps).toEqual([expect.objectContaining({ periods: 3, stratified: true })])
    expect(familyOf('X2_DiffSch_2017')?.notice).toContain('ErwG 15')
  })
})
