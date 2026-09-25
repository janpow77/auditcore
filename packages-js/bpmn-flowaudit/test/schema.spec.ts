import { describe, expect, it } from 'vitest'
import { flowauditModdleDescriptor, FLOWAUDIT_NAMESPACE } from '../src/schema/descriptor'
import { createModdle, loadDefinitions, saveDefinitions } from '../src/model/load'
import { modelFromDefinitions } from '../src/model/buildModel'
import { readExtensions, setExtensionsDirect } from '../src/model/extensions'
import { protectUnknownElements, restoreUnknownElements } from '../src/model/unknownElements'
import { TYPES } from '../src/schema/spec'
import { fixture, modelOf } from './helpers'

function snapshot(model: Awaited<ReturnType<typeof modelOf>>) {
  return JSON.stringify({ info: model.info, ext: model.elements.map((el) => [el.id, el.extensions, el.attributes]) })
}

describe('moddle descriptor', () => {
  it('keeps namespace, prefix and tagAlias of schema 1.0', () => {
    expect(flowauditModdleDescriptor.uri).toBe(FLOWAUDIT_NAMESPACE)
    expect(flowauditModdleDescriptor.prefix).toBe('flowaudit')
    expect(flowauditModdleDescriptor.xml).toEqual({ tagAlias: 'lowerCase' })
  })

  it('defines one moddle type per schema type plus text types', () => {
    const names = flowauditModdleDescriptor.types.map((type) => type.name)
    for (const spec of Object.values(TYPES)) expect(names).toContain(spec.moddle)
    expect(names).toEqual(expect.arrayContaining(['Beschreibung', 'Schlagwort', 'Fonds', 'Kriterium', 'Empfehlung', 'Bemerkung']))
  })
})

describe('round trip', () => {
  it('reads 1.0 legacy data (text, value attribute, notiz) and keeps it on write', async () => {
    const xml = fixture('legacy-1.0.bpmn')
    const loaded = await loadDefinitions(xml)
    const model = modelFromDefinitions(loaded.definitions)
    const pruefen = model.byId.get('Task_Pruefen')
    expect(pruefen?.extensions.legalBases).toEqual([{ text: '§ 44 LHO; Art. 74 VO (EU) 2021/1060' }])
    expect(pruefen?.extensions.internalNote).toBe('Nur bei Anträgen über dem Schwellenwert.')
    const bescheid = model.byId.get('Task_Bescheid')
    expect(bescheid?.extensions.legalBases).toEqual([{ text: '§ 35 VwVfG' }])
    expect(bescheid?.extensions.internalNote).toBe('Altform der Notiz')
    expect(pruefen?.attributes.costEstimate).toBe('30')

    const out = await saveDefinitions(loaded)
    expect(out).toContain('<flowaudit:rechtsgrundlage>§ 44 LHO; Art. 74 VO (EU) 2021/1060</flowaudit:rechtsgrundlage>')
    expect(out).toContain('camunda:property')
    expect(snapshot(await modelOf(out))).toBe(snapshot(model))
  })

  it('reads every 1.1 type and survives import → export → import unchanged', async () => {
    const xml = fixture('schema-1.1.bpmn')
    const model = await modelOf(xml)
    expect(model.info?.title).toBe('Bewilligung und Auszahlung (Muster)')
    expect(model.info?.funds).toEqual(['efre', 'esf_plus'])
    expect(model.info?.keywords).toEqual(['Bewilligung', 'Auszahlung'])
    expect(model.info?.risks?.[0]?.controls).toEqual(['K1'])
    const loaded = await loadDefinitions(xml)
    const out = await saveDefinitions(loaded)
    expect(snapshot(await modelOf(out))).toBe(snapshot(model))
  })

  it('reads the 1.1 extensions of tasks, events and data objects', async () => {
    const model = await modelOf(fixture('schema-1.1.bpmn'))
    const task = model.byId.get('Task_Pruefen')
    expect(task?.extensions.legalBases[0]).toMatchObject({ act: 'Verordnung (EU) 2021/1060', article: '73', paragraph: '2', point: 'b' })
    expect(task?.extensions.controls[0]).toMatchObject({ id: 'K1', keyControl: true, description: 'Zweite Person zeichnet die Checkliste gegen.' })
    expect(task?.extensions.auditSteps[0]).toMatchObject({ id: 'PS1', result: 'erfuellt', remark: 'Gegenzeichnung vorhanden.' })
    expect(task?.extensions.crossReferences[0]).toEqual({ kind: 'prueffeld', key: '3.21', document: 'Antragsprüfcheckliste Muster V 1.0' })
    expect(model.byId.get('Task_Bewilligen')?.extensions.findings[0]).toMatchObject({ reference: 'T15 F1', findingType: 'formell', recommendation: 'Begründung im Vermerk festhalten.' })
    expect(model.byId.get('Timer_Frist')?.extensions.deadlines[0]!.legalBases?.[0]?.article).toBe('74')
    expect(model.byId.get('DataRef_Vermerk')?.extensions.evidence[0]).toMatchObject({ storageLocation: 'eAkte', itSystem: 'Fördersystem' })
    expect(model.byId.get('Task_Pruefen')?.actor).toMatchObject({ role: 'zgs', displayName: 'Musterförderbank' })
  })

  it('preserves unknown flowaudit elements (schema 1.1 requirement)', async () => {
    const loaded = await loadDefinitions(fixture('schema-1.1.bpmn'))
    const out = await saveDefinitions(loaded)
    expect(out).toMatch(/<flowaudit:zukunft wert="bleibt">\s*<flowaudit:teil>unbekannt<\/flowaudit:teil>\s*<\/flowaudit:zukunft>/)
    expect(out).not.toContain('flowauditUnbekannt')
  })

  it('leaves XML without unknown elements untouched', () => {
    const xml = fixture('legacy-1.0.bpmn')
    expect(protectUnknownElements(xml)).toBe(xml)
    expect(restoreUnknownElements(xml)).toBe(xml)
  })
})

describe('writing extensions', () => {
  it('writes children in schema order after foreign extensions', async () => {
    const loaded = await loadDefinitions(fixture('legacy-1.0.bpmn'))
    const model = modelFromDefinitions(loaded.definitions)
    expect(model).toBeTruthy()
    const task = (loaded.definitions.get('rootElements') as { get(n: string): unknown }[])[0]!.get('flowElements') as never[]
    const bo = (task as { id: string }[]).find((el) => el.id === 'Task_Pruefen') as never
    setExtensionsDirect(bo, { markers: [{ type: 'pruefpunkt' }], actor: undefined, auditReferences: [{ keyRequirement: '4', assessmentCriterion: '4.1' }] }, createModdle())
    const out = await saveDefinitions(loaded)
    const order = [...out.matchAll(/<(camunda:properties|flowaudit:\w+)/g)].map((m) => m[1]).slice(0, 5)
    expect(order).toEqual(['camunda:properties', 'flowaudit:rechtsgrundlage', 'flowaudit:interneNotiz', 'flowaudit:kennzeichen', 'flowaudit:pruefbezug'])
    expect(readExtensions(bo).markers).toEqual([{ type: 'pruefpunkt' }])
  })

  it('removes extensionElements when the last entry disappears', async () => {
    const loaded = await loadDefinitions(fixture('legacy-1.0.bpmn'))
    const process = (loaded.definitions.get('rootElements') as { get(n: string): unknown }[])[0]
    const bo = (process!.get('flowElements') as { id: string }[]).find((el) => el.id === 'Task_Bescheid') as never
    setExtensionsDirect(bo, { legalBases: [], internalNote: '' }, createModdle())
    const out = await saveDefinitions(loaded)
    const bescheid = /<bpmn:task id="Task_Bescheid"[\s\S]*?<\/bpmn:task>/.exec(out)?.[0] ?? ''
    expect(bescheid).not.toContain('extensionElements')
  })

  it('writes booleans and lists as schema strings', async () => {
    const moddle = createModdle()
    const loaded = await loadDefinitions(fixture('legacy-1.0.bpmn'), moddle)
    const process = (loaded.definitions.get('rootElements') as { get(n: string): unknown }[])[0]
    const bo = (process!.get('flowElements') as { id: string }[]).find((el) => el.id === 'Task_Bescheid') as never
    setExtensionsDirect(bo, { controls: [{ id: 'K9', keyControl: false }], risks: [{ id: 'R9', controls: ['K9', 'K10'] }] }, moddle)
    const out = await saveDefinitions(loaded)
    expect(out).toContain('schluesselkontrolle="false"')
    expect(out).toContain('kontrollen="K9 K10"')
  })
})
