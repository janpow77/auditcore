import { describe, expect, it, vi } from 'vitest'
import { editorAccess, headlessAccess } from '../src/model/access'
import { cleanInfo, headerOf, infoFromLegacy, legacyFromInfo, readDiagramInfoFromEditor, setDiagramInfo, writeDiagramInfo } from '../src/model/diagramInfo'
import { readFlowstatValues, writeFlowstatValues } from '../src/model/flowstatAttributes'
import { loadDefinitions, saveDefinitions, EMPTY_DIAGRAM } from '../src/model/load'
import { modelFromDefinitions, modelFromEditor, readDiagramInfo } from '../src/model/buildModel'
import { camelToSnake, fromWire, snakeToCamel, toWire } from '../src/model/wire'
import { applyDirection, keepDirection } from '../src/layout/flowDirection'
import type { Canvas, DiagramElement, ElementRegistry, EventCallback, ModdleElement, Modeling } from '../src/diagram/services'
import { fixture } from './helpers'

describe('diagram info', () => {
  it('reads, writes and migrates legacy header columns', async () => {
    const loaded = await loadDefinitions(EMPTY_DIAGRAM)
    expect(readDiagramInfo(loaded.definitions)).toBeNull()
    const info = infoFromLegacy({ name: 'Ablauf', header_title: 'Kopf', header_color: '#123456', process_owner: 'Referat 1', version: 3, is_archived: true })
    expect(info).toMatchObject({ title: 'Kopf', headerColor: '#123456', processOwner: 'Referat 1', version: '3', status: 'archiviert', schemaVersion: '1.1' })
    expect(setDiagramInfo(loaded.definitions, { ...info, keywords: ['A'], legalBases: [{ act: 'LHO', section: '44' }] }, loaded.moddle)).toBe(true)
    const xml = await saveDefinitions(loaded)
    expect(xml).toContain('<flowaudit:diagrammInfo schemaVersion="1.1" titel="Kopf"')
    expect(xml).toContain('<flowaudit:rechtsgrundlage norm="LHO" paragraph="44">§ 44 LHO</flowaudit:rechtsgrundlage>')
    const back = readDiagramInfo((await loadDefinitions(xml)).definitions)
    expect(back?.keywords).toEqual(['A'])
    expect(legacyFromInfo(back ?? {})).toMatchObject({ header_title: 'Kopf', header_color: '#123456', is_archived: true })
  })

  it('lets XML data win over legacy columns and drops blanks', () => {
    expect(infoFromLegacy({ header_title: 'Alt' }, { title: 'Neu', subtitle: '' }).title).toBe('Neu')
    expect(cleanInfo({ title: '  T  ', keywords: [], subtitle: ' ' })).toEqual({ title: 'T', schemaVersion: '1.1' })
    expect(headerOf(null, 'Fallback')).toEqual({ title: 'Fallback', subtitle: '', color: '#1976d2', textColor: '#ffffff' })
  })

  it('writes through modeling in the editor', async () => {
    const loaded = await loadDefinitions(fixture('schema-1.1.bpmn'))
    const collaboration = (loaded.definitions.get('rootElements') as ModdleElement[])[0]
    const root = { id: 'Collaboration_Muster', type: 'bpmn:Collaboration', businessObject: collaboration } as DiagramElement
    const canvas = { getRootElement: () => root } as unknown as Canvas
    expect(readDiagramInfoFromEditor({ canvas })?.title).toBe('Bewilligung und Auszahlung (Muster)')
    const modeling = { updateModdleProperties: vi.fn() } as unknown as Modeling
    writeDiagramInfo({ canvas, modeling, moddle: loaded.moddle }, { title: 'Neu' })
    expect(modeling.updateModdleProperties).toHaveBeenCalledTimes(1)
  })
})

describe('model access', () => {
  it('reads and writes headless, renames and colours', async () => {
    const loaded = await loadDefinitions(fixture('legacy-1.0.bpmn'))
    const access = headlessAccess(loaded.definitions, loaded.moddle)
    expect(access.has('Task_Pruefen')).toBe(true)
    access.write('Task_Pruefen', { markers: [{ type: 'dokument' }] })
    access.rename('Task_Pruefen', 'Neu')
    access.setColor('Task_Pruefen', { fill: '#c8e6c9', stroke: '#1b5e20' })
    access.setColor('Task_Bescheid', null)
    const model = modelFromDefinitions((await loadDefinitions(await saveDefinitions(loaded))).definitions)
    expect(model.byId.get('Task_Pruefen')).toMatchObject({ name: 'Neu', color: { fill: '#c8e6c9', stroke: '#1b5e20' } })
    expect(model.byId.get('Task_Pruefen')?.extensions.markers).toEqual([{ type: 'dokument' }])
  })

  it('delegates to modeling in the editor', async () => {
    const loaded = await loadDefinitions(fixture('legacy-1.0.bpmn'))
    const process = (loaded.definitions.get('rootElements') as ModdleElement[])[0]
    const bo = (process.get('flowElements') as ModdleElement[]).find((el) => el.id === 'Task_Pruefen') as ModdleElement
    const element = { id: 'Task_Pruefen', type: 'bpmn:Task', businessObject: bo } as DiagramElement
    const modeling = { updateProperties: vi.fn(), updateModdleProperties: vi.fn(), setColor: vi.fn() } as unknown as Modeling
    const registry = { get: (id: string) => (id === 'Task_Pruefen' ? element : undefined) } as unknown as ElementRegistry
    const access = editorAccess({ canvas: {} as Canvas, elementRegistry: registry, modeling, moddle: loaded.moddle })
    access.write('Task_Pruefen', { markers: [{ type: 'risiko' }] })
    access.rename('Task_Pruefen', 'X')
    access.setColor('Task_Pruefen', null)
    access.write('Fehlt', { markers: [] })
    expect(access.name('Task_Pruefen')).toBe('Antrag prüfen')
    expect(access.read('Task_Pruefen').legalBases).toHaveLength(1)
    expect(modeling.updateModdleProperties).toHaveBeenCalledTimes(1)
    expect(modeling.updateProperties).toHaveBeenCalledWith(element, { name: 'X' })
    expect(modeling.setColor).toHaveBeenCalledWith([element], { fill: null, stroke: null })
  })

  it('builds the model from a running editor with current bounds', async () => {
    const loaded = await loadDefinitions(fixture('legacy-1.0.bpmn'))
    const process = (loaded.definitions.get('rootElements') as ModdleElement[])[0]
    const root = { id: 'Process_Alt', type: 'bpmn:Process', businessObject: process } as DiagramElement
    const shape = { id: 'Task_Pruefen', type: 'bpmn:Task', businessObject: {} as ModdleElement, x: 1, y: 2, width: 3, height: 4 } as DiagramElement
    const model = modelFromEditor({ canvas: { getRootElement: () => root } as unknown as Canvas, elementRegistry: { getAll: () => [shape] } as unknown as ElementRegistry })
    expect(model.byId.get('Task_Pruefen')?.bounds).toEqual({ x: 1, y: 2, width: 3, height: 4 })
  })
})

describe('FlowStat values in the editor', () => {
  it('reads aliases and writes canonical names, removing aliases', () => {
    const bo = { id: 'T', $attrs: { duration: '15', cost: '4' }, get: (n: string) => (n === 'name' ? 'Prüfen' : undefined) } as unknown as ModdleElement
    expect(readFlowstatValues(bo)).toMatchObject({ duration_minutes: 15, cost: 4 })
    const modeling = { updateProperties: vi.fn() }
    writeFlowstatValues({ id: 'T', type: 'bpmn:Task', businessObject: bo }, { duration_minutes: 20, cost: null }, modeling)
    expect(modeling.updateProperties).toHaveBeenCalledWith(expect.anything(), { duration: undefined, durationEstimated: '20', durationUnit: 'Minuten', cost: undefined, costEstimate: undefined })
  })
})

describe('wire JSON', () => {
  it('converts keys between camelCase and snake_case recursively', () => {
    expect(camelToSnake('assessmentCriterion')).toBe('assessment_criterion')
    expect(snakeToCamel('valid_from')).toBe('validFrom')
    const wire = toWire({ validFrom: '2026-01-01', legalBases: [{ shortTitle: 'CPR' }] })
    expect(wire).toEqual({ valid_from: '2026-01-01', legal_bases: [{ short_title: 'CPR' }] })
    expect(fromWire(wire)).toEqual({ validFrom: '2026-01-01', legalBases: [{ shortTitle: 'CPR' }] })
  })
})

describe('flow direction', () => {
  function editor(pools: DiagramElement[]) {
    const listeners: EventCallback[] = []
    const modeling = { updateModdleProperties: vi.fn(), resizeShape: vi.fn() }
    const services: Record<string, unknown> = {
      elementRegistry: { filter: (predicate: (e: DiagramElement) => boolean) => pools.filter(predicate) },
      modeling,
      eventBus: { on: (_e: string, _p: number, cb: EventCallback) => listeners.push(cb), off: vi.fn() },
    }
    return { editor: { get: <T,>(name: string) => services[name] as T }, modeling, listeners }
  }
  const pool = (horizontal?: boolean): DiagramElement =>
    ({ id: 'P', type: 'bpmn:Participant', x: 0, y: 0, width: 600, height: 250, businessObject: { $type: 'bpmn:Participant' }, di: { get: () => horizontal } }) as unknown as DiagramElement

  it('rotates pools and swaps width and height', () => {
    const { editor: e, modeling } = editor([pool(undefined)])
    expect(applyDirection(e, 'senkrecht')).toBe(1)
    expect(modeling.resizeShape).toHaveBeenCalledWith(expect.anything(), { x: 0, y: 0, width: 250, height: 600 })
    expect(applyDirection(editor([pool(true)]).editor, 'waagerecht')).toBe(1)
  })

  it('keeps new pools on the chosen direction', () => {
    const { editor: e, modeling, listeners } = editor([])
    const stop = keepDirection(e, () => 'senkrecht')
    listeners[0]({ context: { shape: pool(true) } })
    expect(modeling.updateModdleProperties).toHaveBeenCalledTimes(1)
    stop()
  })
})
