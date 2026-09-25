import { describe, expect, it } from 'vitest'
import { approve, checkCollection, diagramReferences, groupOverview, sha256Xml, targetActualPairs, verifyApproval } from '../src/collection/analysis'
import { CollectionError, DiagramCollection } from '../src/collection/collection'
import { COLLECTION_SCHEMA, idFromName } from '../src/collection/collectionData'
import { elementsForKey } from '../src/collection/excerpt'
import { fixture, modelOf } from './helpers'

async function sample(): Promise<DiagramCollection> {
  const collection = new DiagramCollection('s', 'Sammlung')
  collection.createFolder('antrag', 'Antragsverfahren')
  collection.createFolder('antrag-sub', 'Unterordner', 'antrag')
  collection.createFolder('pruefung', 'Prüfung')
  collection.createTag('kern', 'Kernprozess', '#1976d2')
  collection.addDiagram('muster', { folderId: 'antrag', tags: ['kern'], model: await modelOf(fixture('schema-1.1.bpmn')) })
  collection.addDiagram('alt', { folderId: 'antrag-sub', model: await modelOf(fixture('legacy-1.0.bpmn')) })
  collection.addDiagram('anreicherung', { name: 'Anreicherung', folderId: 'pruefung', model: await modelOf(fixture('enrichment.bpmn')) })
  return collection
}

describe('DiagramCollection', () => {
  it('builds a folder tree with ordered diagrams and titles from the info', async () => {
    const collection = await sample()
    const tree = collection.tree()
    expect(tree.subfolders.map((f) => f.folder?.id)).toEqual(['antrag', 'pruefung'])
    expect(tree.subfolders[0]!.subfolders[0]!.diagrams.map((d) => d.id)).toEqual(['alt'])
    expect(collection.entry('muster').name).toBe('Bewilligung und Auszahlung (Muster)')
    expect(collection.diagramsIn('antrag').map((d) => d.id)).toEqual(['muster', 'alt'])
  })

  it('moves diagrams and folders and prevents cycles', async () => {
    const collection = await sample()
    collection.move('anreicherung', 'antrag', 0)
    expect(collection.inFolder('antrag').map((d) => d.id)).toEqual(['anreicherung', 'muster'])
    expect(() => collection.moveFolder('antrag', 'antrag-sub')).toThrow(CollectionError)
    collection.moveFolder('antrag-sub', null)
    expect(collection.subfolders(null).map((f) => f.id)).toContain('antrag-sub')
    expect(() => collection.removeFolder('antrag')).toThrow('nicht leer')
    collection.setOrder('antrag', ['muster', 'anreicherung'])
    expect(collection.inFolder('antrag')[0]!.id).toBe('muster')
    expect(() => collection.setTags('muster', ['unbekannt'])).toThrow('Unbekannte Tags')
  })

  it('searches, filters by tag/status and finds elements by domain key', async () => {
    const collection = await sample()
    expect(collection.search('auszahlung').map((d) => d.id)).toEqual(['muster'])
    expect(collection.search('', { status: 'freigegeben' }).map((d) => d.id)).toEqual(['muster'])
    expect(collection.search('', { tag: 'kern' })).toHaveLength(1)
    expect(collection.elementsForKey('bk', '2.3')).toEqual([['muster', 'Task_Pruefen'], ['muster', 'Task_Bewilligen']])
    expect(collection.elementsForKey('feststellung_ref', 'T15 F1')).toEqual([['muster', 'Task_Bewilligen']])
    expect(collection.elementsForKey('rolle', 'zgs')).toEqual([['muster', 'Lane_ZGS']])
    expect(elementsForKey(await modelOf(fixture('schema-1.1.bpmn')), 'prueffeld', '3.21')).toEqual(['Task_Pruefen'])
  })

  it('serialises and restores the collection', async () => {
    const collection = await sample()
    const data = collection.toData()
    expect(data.schema).toBe(COLLECTION_SCHEMA)
    const restored = DiagramCollection.fromData(JSON.parse(JSON.stringify(data)))
    expect(restored.toData()).toEqual(data)
    expect(() => DiagramCollection.fromData({ ...data, schema: 'x' })).toThrow('Sammlungsschema')
  })

  it('creates valid ids from names', () => {
    expect(idFromName('Antragsverfahren Förderung', new Set())).toBe('antragsverfahren-foerderung')
    expect(idFromName('A', new Set(['a']))).toBe('a-2')
  })
})

describe('collection analysis', () => {
  it('summarises a group with status, legal basis coverage and KA coverage', async () => {
    const overview = groupOverview(await sample(), { folderId: 'antrag', referenceDate: '2026-09-25' })
    expect(overview.count).toBe(2)
    expect(overview.statusDistribution).toEqual({ freigegeben: 1, ohne_status: 1 })
    expect(overview.keyRequirementCoverage[2]).toEqual(['muster'])
    expect(overview.legalBasisCoverage).toBeGreaterThan(0.5)
  })

  it('resolves references across diagrams and reports unresolved ones', async () => {
    const collection = await sample()
    const caller = await modelOf(
      fixture('legacy-1.0.bpmn').replace('<bpmn:task id="Task_Bescheid"', '<bpmn:callActivity id="Call_1" name="Muster aufrufen" calledElement="Process_Verwaltung" /><bpmn:callActivity id="Call_2" calledElement="Unbekannt" /><bpmn:task id="Task_Bescheid"'),
    )
    collection.update('alt', caller)
    const references = diagramReferences(collection)
    expect(references.find((r) => r.sourceElement === 'Call_1')?.targetDiagram).toBe('muster')
    expect(checkCollection(collection).map((i) => i.ruleId)).toContain('BPMN-K001')
  })

  it('pairs actual-state diagrams with their target', async () => {
    const collection = await sample()
    const actual = await modelOf(fixture('schema-1.1.bpmn').replace('variante="soll"', 'variante="ist" bezugDiagramm="muster"').replace(/Process_Verwaltung/g, 'Process_Ist').replace(/Process_Beg/g, 'Process_Beg_Ist'))
    collection.addDiagram('ist', { model: actual })
    expect(targetActualPairs(collection)).toEqual([['ist', 'muster']])
  })

  it('records immutable approvals with SHA-256', async () => {
    const collection = await sample()
    const xml = fixture('schema-1.1.bpmn')
    const approval = await approve(collection, 'muster', xml, '1.2', { approvedBy: 'Referatsleitung', approvedOn: '2025-12-15' })
    expect(approval.sha256).toBe(await sha256Xml(xml))
    expect(approval.sha256).toMatch(/^[0-9a-f]{64}$/)
    await expect(approve(collection, 'muster', `${xml} `, '1.2')).rejects.toThrow('bereits freigegeben')
    expect(await verifyApproval(collection, 'muster', xml)).toBeNull()
    expect((await verifyApproval(collection, 'muster', `${xml}\n`))?.ruleId).toBe('BPMN-K008')
  })
})
