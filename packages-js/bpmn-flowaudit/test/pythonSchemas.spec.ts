/**
 * Conformance with the JSON schemas of `auditcore_bpmn` (collection,
 * profile, validation report). Runs when the Python package is present in
 * the checkout; the schemas are not copied.
 */
import { existsSync, readFileSync } from 'node:fs'
import { join } from 'node:path'
import Ajv2020 from 'ajv/dist/2020'
import { describe, expect, it } from 'vitest'
import { DiagramCollection } from '../src/collection/collection'
import { toWire } from '../src/model/wire'
import { bundledProfiles } from '../src/profile/bundled'
import { reportToWire, validateModel } from '../src/validation/validate'
import { fixture, modelOf, TEST_PROFILE } from './helpers'

const SCHEMAS = join(process.cwd(), '../../packages/auditcore_bpmn/src/auditcore_bpmn/schemas')
const present = existsSync(SCHEMAS)

function validator(name: string) {
  const ajv = new Ajv2020({ allErrors: true, strict: false })
  return ajv.compile(JSON.parse(readFileSync(join(SCHEMAS, name), 'utf-8')))
}

describe.skipIf(!present)('JSON schemas of auditcore_bpmn', () => {
  it('accepts the collection written by DiagramCollection', async () => {
    const collection = new DiagramCollection()
    collection.createFolder('antrag', 'Antragsverfahren')
    collection.createFolder('unter', 'Unterordner', 'antrag')
    collection.createTag('kern', 'Kern', '#1976d2')
    collection.addDiagram('muster', { folderId: 'antrag', tags: ['kern'], model: await modelOf(fixture('schema-1.1.bpmn')) })
    collection.addDiagram('anreicherung', { model: await modelOf(fixture('enrichment.bpmn')) })
    const validate = validator('diagram-collection-1.schema.json')
    const wire = toWire(collection.toData())
    expect(validate(wire), JSON.stringify(validate.errors)).toBe(true)
  })

  it('accepts the bundled profiles and the synthetic test profile', () => {
    const validate = validator('profile-1.schema.json')
    for (const profile of [...bundledProfiles(), TEST_PROFILE]) expect(validate(profile), `${profile.id}: ${JSON.stringify(validate.errors)}`).toBe(true)
  })

  it('accepts the validation report of the browser validation', async () => {
    const validate = validator('validation-report-1.schema.json')
    const report = validateModel(await modelOf(fixture('schema-1.1.bpmn')), { profile: TEST_PROFILE, referenceDate: '2026-09-25' })
    expect(report.issues.length).toBeGreaterThan(0)
    expect(validate(reportToWire(report)), JSON.stringify(validate.errors)).toBe(true)
  })
})
