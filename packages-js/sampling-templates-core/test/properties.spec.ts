import { describe, expect, it } from 'vitest'
import { createTranslate } from '../src/i18n/messages'
import { isNumber, lt } from '../src/excel/index'
import { defaultInputs, findField } from '../src/model/definition'
import { optionalOf, resultCellsOf } from '../src/model/dependence'
import { createContext, type AvailableSheet } from '../src/model/sheet'
import { SHEETS, findAvailableSheet } from '../src/sheets/registry'
import type { CellValue } from '../src/model/types'
import { carriedLimitations, isQualified, limitationsOf } from '../src/view/limits'
import { contextFor } from '../src/workspace/compute'
import { caseState, caseWorkspace, compareCase, goldenFiles, readGoldenFile, sameValue, selectedSheets, type GoldenCase } from './golden'

/**
 * Eigenschaften, die für jedes Blatt gelten müssen (Auflagen der Gesamtabnahme):
 *
 * 1. Sind alle Pflichteingaben vorhanden, zeigt die Webfassung in jeder Zelle,
 *    was die Vorlage zeigt (vollständige Zufallsbelegungen: keine offene Zelle;
 *    ausgenommen der Abgleich mit einem leeren Blatt 02, `local`).
 * 2. Fehlt genau eine Eingabe, die nicht für sich freiwillig ist, und ändert das
 *    in der Vorlage ein Ergebnis des Blatts, dann ist dieses Ergebnis in der
 *    Webfassung offen oder trägt einen Hinweis in Warnfarbe (nie ein
 *    uneingeschränkt gewürdigtes Ergebnis).
 * 3. Eine negative Fehlerquote oder ein negativer extrapolierter Fehler trägt
 *    einen Hinweis in Warnfarbe.
 */
const t = createTranslate()
const casesOf = (file: string): GoldenCase[] => readGoldenFile(file)
const setsOf = (sheet: AvailableSheet, part: string): GoldenCase[] => goldenFiles(sheet.id).filter((file) => file.includes(part)).flatMap(casesOf)

/** Zellen des Blatts, an denen sein Ergebnis hängt, soweit der Fall sie enthält. */
function resultCells(sheet: AvailableSheet, golden: GoldenCase): string[] {
  return resultCellsOf(sheet).filter((cell) => `${sheet.id}!${cell}` in golden.erwartet)
}

/** Ist die im Lückenfall entfernte Eingabe für sich freiwillig (leer heißt „keine“)? Dann ist ihr Fehlen keine Lücke. */
function isVoluntary(sheet: AvailableSheet, gap: GoldenCase): boolean {
  const reference = / Lücke (\S+)/.exec(gap.name)?.[1] ?? ''
  const [id, cell] = reference.includes('!') ? (reference.split('!') as [string, string]) : [sheet.id, reference]
  const owner = findAvailableSheet(id, SHEETS)
  const field = owner ? findField(owner.definition, cell) : undefined
  return field !== undefined && optionalOf(field) === true
}

/** Ist das Ergebnis der Webfassung durch einen Hinweis in Warnfarbe eingeschränkt? */
function qualified(sheet: AvailableSheet, golden: GoldenCase): boolean {
  const all = caseWorkspace(sheet, golden)
  // Listenblatt (Blatt 17): ein Fall ist eine Stichprobeneinheit ohne Arbeitsstand.
  const list = sheet.definition.layout === 'list'
  const state = caseState(sheet, golden)
  const inputs = list ? { ...defaultInputs(sheet.definition), ...golden.eingaben } : ((state.sheets[sheet.id] ?? {}) as Record<string, CellValue>)
  const context = list ? createContext() : contextFor(sheet.id, state, all)
  return isQualified([...limitationsOf(sheet, inputs, all[sheet.id] ?? {}, context, t), ...carriedLimitations(sheet, context, t)])
}

/** Vollständiger Ausgangsfall eines Lückenfalls: „<Kennung> Basis vollständig …“ zu „<Kennung> Lücke <Zelle> …“. */
function baseOf(gap: GoldenCase, cases: readonly GoldenCase[]): GoldenCase | undefined {
  const at = gap.name.indexOf(' Lücke ')
  return at < 0 ? undefined : cases.find((candidate) => candidate.name.startsWith(`${gap.name.slice(0, at)} Basis`))
}

describe('Eigenschaften über alle Blätter', () => {
  for (const sheet of selectedSheets()) {
    it(`${sheet.id}: vollständige Zufallsbelegungen – keine Zelle offen, die in der Vorlage einen Wert hat`, () => {
      const open = setsOf(sheet, 'zufall').flatMap((golden) => compareCase(sheet, golden).explained.filter((entry) => !entry.deviation.local).map((entry) => `${golden.name}: ${entry.cell}`))
      expect(open.slice(0, 20)).toEqual([])
    })

    it(`${sheet.id}: fehlt eine Eingabe, die das Ergebnis der Vorlage ändert, ist es offen oder trägt einen Hinweis in Warnfarbe`, () => {
      const cases = setsOf(sheet, 'abnahme-luecken')
      const silent: string[] = []
      for (const gap of cases) {
        const base = baseOf(gap, cases)
        if (!base || isVoluntary(sheet, gap)) continue
        const results = caseWorkspace(sheet, gap)[sheet.id] ?? {}
        const changed = resultCells(sheet, gap).filter((cell) => !sameValue(base.erwartet[`${sheet.id}!${cell}`] ?? null, gap.erwartet[`${sheet.id}!${cell}`] ?? null) && isNumber(results[cell]))
        if (changed.length && !qualified(sheet, gap)) silent.push(`${gap.name}: ${changed.join(', ')}`)
      }
      expect(silent.slice(0, 40)).toEqual([])
    })

    it(`${sheet.id}: negative Fehlerquote oder negativer extrapolierter Fehler trägt einen Hinweis in Warnfarbe`, () => {
      const silent: string[] = []
      for (const golden of goldenFiles(sheet.id).flatMap(casesOf)) {
        const results = caseWorkspace(sheet, golden)[sheet.id] ?? {}
        const negative = resultCells(sheet, golden).filter((cell) => isNumber(results[cell]) && lt(results[cell] as number, 0))
        if (negative.length && !qualified(sheet, golden)) silent.push(`${golden.name}: ${negative.join(', ')}`)
      }
      expect(silent.slice(0, 40)).toEqual([])
    })
  }
}, 300_000)
