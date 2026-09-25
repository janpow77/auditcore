/**
 * Local parity test against real user diagrams. The diagrams must never be
 * committed; the test only runs when `BPMN_LOCAL_FIXTURES` points to a
 * directory with `.bpmn`/`.xml` files, otherwise it is skipped.
 *
 * Per diagram: headless round trip (model before = model after), enrichment
 * suggestions, validation and neutralisation must run without error.
 */

import { readdirSync, readFileSync } from 'node:fs'
import { join } from 'node:path'
import { describe, expect, it } from 'vitest'
import { collectSuggestions } from '../src/enrichment/suggestions'
import { modelFromDefinitions } from '../src/model/buildModel'
import { loadDefinitions, saveDefinitions } from '../src/model/load'
import { neutralize } from '../src/neutralize/neutralize'
import { validateModel } from '../src/validation/validate'
import { TEST_PROFILE } from './helpers'

const directory = process.env.BPMN_LOCAL_FIXTURES

function snapshot(model: ReturnType<typeof modelFromDefinitions>): string {
  return JSON.stringify(model.elements.map((el) => [el.id, el.type, el.name, el.documentation, el.extensions, el.bounds, el.color, el.sourceId, el.targetId]))
}

describe.skipIf(!directory)('local parity with user diagrams', () => {
  it('round-trips, enriches, validates and neutralises every diagram', async () => {
    const files = readdirSync(directory as string).filter((name) => /\.(bpmn|xml)$/i.test(name))
    const failures: string[] = []
    let suggestions = 0
    for (const file of files) {
      try {
        const xml = readFileSync(join(directory as string, file), 'utf-8')
        const loaded = await loadDefinitions(xml)
        const before = modelFromDefinitions(loaded.definitions)
        const after = modelFromDefinitions((await loadDefinitions(await saveDefinitions(loaded))).definitions)
        if (snapshot(before) !== snapshot(after)) throw new Error('Rundlauf verändert das Modell')
        suggestions += collectSuggestions(before, { profile: TEST_PROFILE }).length
        validateModel(before, { profile: TEST_PROFILE })
        neutralize(xml, { profile: TEST_PROFILE })
      } catch (error) {
        failures.push(`${file}: ${(error as Error).message}`)
      }
    }
    console.info(`Lokaler Paritätstest: ${files.length - failures.length} ok, ${failures.length} fehlerhaft, ${suggestions} Vorschläge`)
    expect(failures).toEqual([])
  }, 120_000)
})
