import { readFileSync } from 'node:fs'
import Ajv2020 from 'ajv/dist/2020'
import { describe, expect, it } from 'vitest'
import { sheet as sheet03 } from '../src/sheets/03_MUS_1Z/index'
import { openWorkspace } from '../src/workspace/open'
import { saveWorkspace } from '../src/workspace/save'
import { emptyWorkspace, type WorkspaceState } from '../src/workspace/types'

const schema = JSON.parse(readFileSync(new URL('../schema/arbeitsstand.schema.json', import.meta.url), 'utf8')) as object
const validate = new Ajv2020({ strict: true, formats: { 'date-time': true } }).compile(schema)
const state: WorkspaceState = { ...emptyWorkspace(), activeMethod: '03_MUS_1Z', sheets: { '03_MUS_1Z': sheet03.sample.inputs, '17_Unterstichprobe': [{ C5: 'V-1', C6: 5 }] } }

describe('JSON-Schema des Arbeitsstands', () => {
  it('gespeicherte Dateien entsprechen dem Schema', async () => {
    for (const candidate of [state, emptyWorkspace()]) {
      const { file } = await saveWorkspace(candidate)
      expect(validate(JSON.parse(JSON.stringify(file))), JSON.stringify(validate.errors)).toBe(true)
    }
  })

  it('Schema und Laufzeitprüfung lehnen dieselben Verstöße ab', async () => {
    const changes: ((file: Record<string, unknown>) => void)[] = [
      (file) => (file.format = 'anders'),
      (file) => (file.formatVersion = 0),
      (file) => (file.aktiveMethode = 'mit leerzeichen'),
      (file) => (file.blaetter = { '03_MUS_1Z': { c7: 1 } }),
      (file) => (file.blaetter = { '03_MUS_1Z': { C7: [1] } }),
      (file) => (file.blaetter = { 'Blatt!': {} }),
      (file) => (file.ergebnisse = { '03_MUS_1Z': [] }),
      (file) => (file.kopf = { cci: 12 }),
      (file) => (file.blaetter = { '17_Unterstichprobe': [{ name: 'x' }] }),
    ]
    for (const change of changes) {
      const file = JSON.parse(JSON.stringify((await saveWorkspace(state)).file)) as Record<string, unknown>
      change(file)
      expect(validate(file), JSON.stringify(file).slice(0, 80)).toBe(false)
      expect((await openWorkspace(JSON.stringify(file))).ok).toBe(false)
    }
  })
})
