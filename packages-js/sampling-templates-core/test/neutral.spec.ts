import { readFileSync, readdirSync } from 'node:fs'
import { join } from 'node:path'
import { fileURLToPath } from 'node:url'
import { describe, expect, it } from 'vitest'
import { availableSheets } from '../src/sheets/registry'

/**
 * Die Webfassung wird von Prüfbehörden verschiedener Programme und
 * Mitgliedstaaten benutzt. Das ausgelieferte Paket nennt deshalb keine bestimmte
 * Behörde und kein bestimmtes Programm – weder im Quelltext noch in Stilen,
 * Beispielwerten oder der Paketbeschreibung. (Die Sollwerte des Abgleichs unter
 * `test/golden` stammen aus der Vorlage und gehören nicht zum Paket.)
 */
const NAMED = /hessen|hmwvw|wiesbaden|referat z ?6/i
const ROOT = fileURLToPath(new URL('..', import.meta.url))
const VUE = join(ROOT, '..', 'sampling-templates-vue')

function filesIn(directory: string): string[] {
  return readdirSync(directory, { withFileTypes: true }).flatMap((entry) => (entry.isDirectory() ? filesIn(join(directory, entry.name)) : [join(directory, entry.name)]))
}

describe('Keine feste Behörde, kein festes Programm', () => {
  it('Quelltext, Stile, Schema und Paketbeschreibung beider Pakete nennen keine bestimmte Prüfbehörde', () => {
    const shipped = [
      ...filesIn(join(ROOT, 'src')),
      ...filesIn(join(ROOT, 'styles')),
      ...filesIn(join(ROOT, 'schema')),
      join(ROOT, 'README.md'),
      join(ROOT, 'package.json'),
      ...filesIn(join(VUE, 'src')),
      join(VUE, 'README.md'),
      join(VUE, 'package.json'),
    ]
    expect(shipped.length).toBeGreaterThan(150)
    expect(shipped.filter((file) => NAMED.test(readFileSync(file, 'utf8'))).map((file) => file.replace(ROOT, ''))).toEqual([])
  })

  it('Beispielwerte nennen nur erkennbar erfundene Programme und Behörden', () => {
    for (const sheet of availableSheets()) {
      const texts = Object.values(sheet.sample.inputs).filter((value): value is string => typeof value === 'string')
      expect(texts.filter((text) => NAMED.test(text)), sheet.id).toEqual([])
    }
    const report = availableSheets().find((sheet) => sheet.id === '20_Druck_KOM')
    expect(report?.sample.inputs).toMatchObject({ W4: expect.stringContaining('Beispiel'), W5: expect.stringContaining('Beispiel') })
  })
})
