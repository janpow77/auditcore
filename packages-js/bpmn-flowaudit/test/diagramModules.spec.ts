/**
 * diagram-js modules against a real diagram-js instance (core renderer of
 * diagram-js, business objects from bpmn-moddle).
 */

import { afterEach, describe, expect, it, vi } from 'vitest'
import Diagram from 'diagram-js'
import ModelingModule from 'diagram-js/lib/features/modeling'
import PaletteModule from 'diagram-js/lib/features/palette'
import ContextPadModule from 'diagram-js/lib/features/context-pad'
import CreateModule from 'diagram-js/lib/features/create'
import { createModdle } from '../src/model/load'
import { colorContextPadModule, COLOR_PICKER_EVENT, isColorable, setColor } from '../src/diagram/colorContextPad'
import { auditReferenceText, decorationsModule, type FlowauditDecorations } from '../src/diagram/decorations'
import { HIGHLIGHT_CLASSES, highlightModule, type FlowauditHighlight } from '../src/diagram/highlight'
import { rolePaletteModule, type RolePaletteProvider } from '../src/diagram/rolePalette'
import { flowauditEditorOptions } from '../src/diagram/modules'
import { setExtensionsDirect } from '../src/model/extensions'
import { ROLES } from '../src/schema/roles'
import type { DiagramElement, ModdleElement } from '../src/diagram/services'
import { TEST_PROFILE } from './helpers'

type AnyDiagram = { get<T>(name: string): T; destroy(): void }

const moddle = createModdle()
const diagrams: AnyDiagram[] = []

function diagram(): AnyDiagram {
  const container = document.createElement('div')
  document.body.appendChild(container)
  const Constructor = Diagram as unknown as new (options: Record<string, unknown>) => AnyDiagram
  const instance = new Constructor({
    canvas: { container },
    modules: [ModelingModule, PaletteModule, ContextPadModule, CreateModule, decorationsModule, highlightModule, rolePaletteModule, colorContextPadModule, { moddle: ['value', moddle], translate: ['value', (s: string, r?: Record<string, string>) => s.replace(/{(\w+)}/g, (_m, k: string) => r?.[k] ?? k)] }],
    flowaudit: { profile: TEST_PROFILE },
  })
  diagrams.push(instance)
  return instance
}

function addShape(instance: AnyDiagram, bo: ModdleElement, bounds = { x: 100, y: 100, width: 100, height: 80 }): DiagramElement {
  const canvas = instance.get<{ getRootElement(): DiagramElement; addShape(shape: unknown, parent: unknown): DiagramElement }>('canvas')
  const factory = instance.get<{ createShape(attrs: Record<string, unknown>): DiagramElement }>('elementFactory')
  return canvas.addShape(factory.createShape({ id: bo.id, businessObject: bo, ...bounds }), canvas.getRootElement())
}

afterEach(() => {
  for (const instance of diagrams.splice(0)) instance.destroy()
})

describe('decorations', () => {
  it('draws the role band and icon into lanes with an actor', () => {
    const instance = diagram()
    const lane = moddle.create('bpmn:Lane', { id: 'Lane_1', name: 'Bewilligung' })
    setExtensionsDirect(lane, { actor: { role: 'zgs' } }, moddle)
    const shape = addShape(instance, lane, { x: 0, y: 0, width: 600, height: 200 })
    const gfx = instance.get<{ getGraphics(e: unknown): SVGElement }>('elementRegistry').getGraphics(shape)
    const band = gfx.querySelector('.fa-role-band')
    expect(band?.getAttribute('data-role')).toBe('zgs')
    expect(band?.querySelector('rect')?.getAttribute('fill')).toBe(ROLES.zgs.color.fill)
    expect(band?.querySelector('title')?.textContent).toBe('Zwischengeschaltete Stelle')
  })

  it('draws marker badges and the audit reference plaque on tasks', () => {
    const instance = diagram()
    const task = moddle.create('bpmn:Task', { id: 'Task_1' })
    setExtensionsDirect(task, { markers: [{ type: 'vier_augen' }, { type: 'frist', text: '10 Arbeitstage' }], auditReferences: [{ keyRequirement: '2', assessmentCriterion: '2.3' }] }, moddle)
    const shape = addShape(instance, task)
    const gfx = instance.get<{ getGraphics(e: unknown): SVGElement }>('elementRegistry').getGraphics(shape)
    expect(gfx.querySelectorAll('.fa-badge')).toHaveLength(2)
    expect(gfx.querySelector('.fa-badge-frist title')?.textContent).toBe('Frist: 10 Arbeitstage')
    expect(gfx.querySelector('.fa-plaque text')?.textContent).toBe('KA 2 · BK 2.3')
  })

  it('redraws on change and respects visibility', () => {
    const instance = diagram()
    const task = moddle.create('bpmn:Task', { id: 'Task_2' })
    const shape = addShape(instance, task)
    const registry = instance.get<{ getGraphics(e: unknown): SVGElement }>('elementRegistry')
    expect(registry.getGraphics(shape).querySelector('.fa-decoration')).toBeNull()
    setExtensionsDirect(task, { markers: [{ type: 'risiko' }] }, moddle)
    instance.get<{ fire(e: string, p: unknown): void }>('eventBus').fire('element.changed', { element: shape })
    expect(registry.getGraphics(shape).querySelectorAll('.fa-badge')).toHaveLength(1)
    const decorations = instance.get<FlowauditDecorations>('flowauditDecorations')
    decorations.setVisibility({ markers: false })
    expect(registry.getGraphics(shape).querySelector('.fa-badge')).toBeNull()
    expect(decorations.getVisibility().markers).toBe(false)
  })

  it('formats several references', () => {
    expect(auditReferenceText([{ keyRequirement: '2' }, { keyRequirement: '4', assessmentCriterion: '4.1' }])).toBe('KA 2, KA 4 · BK 4.1')
  })
})

describe('highlight', () => {
  it('marks hits and dims the rest; clearing removes all classes', () => {
    const instance = diagram()
    const a = addShape(instance, moddle.create('bpmn:Task', { id: 'A' }))
    const b = addShape(instance, moddle.create('bpmn:Task', { id: 'B' }), { x: 300, y: 100, width: 100, height: 80 })
    const canvas = instance.get<{ hasMarker(e: unknown, m: string): boolean }>('canvas')
    const highlight = instance.get<FlowauditHighlight>('flowauditHighlight')
    expect(highlight.filter(['A', 'Unbekannt'])).toBe(1)
    expect(canvas.hasMarker(a, HIGHLIGHT_CLASSES.filter.hit)).toBe(true)
    expect(canvas.hasMarker(b, HIGHLIGHT_CLASSES.filter.dimmed)).toBe(true)
    highlight.apply('diff', new Map([['B', HIGHLIGHT_CLASSES.diff.hinzugefuegt]]))
    highlight.clear('filter')
    expect(canvas.hasMarker(a, HIGHLIGHT_CLASSES.filter.hit)).toBe(false)
    expect(canvas.hasMarker(b, HIGHLIGHT_CLASSES.diff.hinzugefuegt)).toBe(true)
    highlight.clearAll()
    expect(canvas.hasMarker(b, HIGHLIGHT_CLASSES.diff.hinzugefuegt)).toBe(false)
  })
})

describe('role palette and context pads', () => {
  it('offers one pool entry per role of the profile', () => {
    const instance = diagram()
    const entries = instance.get<{ getEntries(): Record<string, { title: string; group: string }> }>('palette').getEntries()
    const roleEntries = Object.keys(entries).filter((id) => id.startsWith('flowaudit-pool-'))
    expect(roleEntries).toHaveLength(TEST_PROFILE.roles.length)
    expect(entries['flowaudit-pool-vb'].title).toBe('Create pool: Verwaltungsbehörde')
    const provider = instance.get<RolePaletteProvider>('flowauditRolePalette')
    expect(provider.roles().map((r) => r.code)).toContain('rfs')
  })

  it('announces role choice and colour choice through the event bus', () => {
    const instance = diagram()
    const lane = addShape(instance, moddle.create('bpmn:Lane', { id: 'L' }), { x: 0, y: 0, width: 400, height: 100 })
    const task = addShape(instance, moddle.create('bpmn:Task', { id: 'T' }), { x: 500, y: 0, width: 100, height: 80 })
    const listener = vi.fn()
    const eventBus = instance.get<{ on(e: string, cb: (e: unknown) => void): void }>('eventBus')
    eventBus.on('flowaudit.role.choose', listener)
    eventBus.on(COLOR_PICKER_EVENT, listener)
    const contextPad = instance.get<{ getEntries(e: unknown): Record<string, { action: { click: (event: Event) => unknown } }> }>('contextPad')
    const laneEntries = contextPad.getEntries(lane)
    expect(Object.keys(laneEntries)).toEqual(expect.arrayContaining(['flowaudit-assign-role', 'flowaudit-add-lane-role', 'flowaudit-farbe']))
    laneEntries['flowaudit-assign-role'].action.click(new MouseEvent('click'))
    contextPad.getEntries(task)['flowaudit-farbe'].action.click(new MouseEvent('click'))
    expect(listener).toHaveBeenCalledTimes(2)
    expect(contextPad.getEntries(task)['flowaudit-assign-role']).toBeUndefined()
  })

  it('assigns a role through modeling', () => {
    const instance = diagram()
    const lane = addShape(instance, moddle.create('bpmn:Lane', { id: 'L2' }), { x: 0, y: 0, width: 400, height: 100 })
    const updateModdleProperties = vi.fn()
    const provider = instance.get<RolePaletteProvider>('flowauditRolePalette')
    Object.assign(provider as unknown as Record<string, unknown>, { modeling: { updateModdleProperties } })
    provider.assignRole(lane, ROLES.pb)
    expect(updateModdleProperties).toHaveBeenCalledTimes(1)
  })
})

describe('unknown elements guard', () => {
  it('protects on import and restores on export', async () => {
    const { UnknownElementsGuard } = await import('../src/diagram/unknownElementsModule')
    const listeners: Record<string, (e: Record<string, unknown>) => unknown> = {}
    new UnknownElementsGuard({ on: (name: string, _p: number, cb: (e: Record<string, unknown>) => unknown) => (listeners[name] = cb) } as never)
    const xml = '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" xmlns:flowaudit="https://flowaudit.de/bpmn/schema/1.0"><flowaudit:neu/></bpmn:definitions>'
    const protectedXml = listeners['import.parse.start']({ xml }) as string
    expect(protectedXml).toContain('flowauditUnbekannt:neu')
    expect(listeners['saveXML.serialized']({ xml: protectedXml })).toContain('<flowaudit:neu')
    expect(listeners['import.parse.start']({})).toBeUndefined()
  })
})

describe('colour helpers and options', () => {
  it('colours only sensible elements and passes palette colours to modeling', () => {
    expect(isColorable({ id: 'x', type: 'bpmn:Task', businessObject: { $type: 'bpmn:Process' } as ModdleElement })).toBe(false)
    expect(isColorable({ id: 'x', type: 'bpmn:Task', businessObject: { $type: 'bpmn:Task' } as ModdleElement })).toBe(true)
    const modeling = { setColor: vi.fn() }
    setColor(modeling, [{ id: 'x', type: 't', businessObject: {} as ModdleElement }], { fill: '#fff', stroke: '#000' })
    setColor(modeling, [], null)
    expect(modeling.setColor).toHaveBeenCalledTimes(1)
  })

  it('bundles modules, moddle extension and config', () => {
    const options = flowauditEditorOptions({ colorContextPad: true })
    expect(options.additionalModules).toHaveLength(5)
    expect(Object.keys(options.moddleExtensions)).toEqual(['flowaudit'])
    expect(options.config.flowaudit).toMatchObject({ colorContextPad: true })
  })
})
