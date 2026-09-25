import { readdirSync, readFileSync } from 'node:fs'
import { join } from 'node:path'

import { createModdle } from '../../src'

export const FIXTURE_DIR = join(__dirname, '..', 'fixtures')

export function readFixture(relativePath: string): string {
  return readFileSync(join(FIXTURE_DIR, relativePath), 'utf8')
}

export function listFixtures(directory: string): string[] {
  return readdirSync(join(FIXTURE_DIR, directory))
    .filter((name) => /\.(bpmn|xml)$/i.test(name))
    .map((name) => `${directory}/${name}`)
}

/** Serialisiert XML über ein frisches moddle – Vergleichsbasis für Rundläufe. */
export async function canonicalXml(xml: string, extensions: Record<string, unknown> = {}): Promise<string> {
  const moddle = createModdle(extensions)
  const { rootElement } = await moddle.fromXML(xml, 'bpmn:Definitions')
  const { xml: result } = await moddle.toXML(rootElement, { format: true })
  return result
}
