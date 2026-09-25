import { describe, expect, it } from 'vitest'

import { getBusinessObject } from '../src'
import { getReplaceOptions } from '../src/replace/ReplaceOptions'
import { childrenOfType, createKit } from './helpers/modeling'

describe('Ersetzen („Morphen“)', () => {
  it('ersetzt Aufgabe durch Benutzeraufgabe unter Erhalt von Kennung, Name, Dokumentation und Erweiterungen', async () => {
    const kit = await createKit()
    const task = kit.create('bpmn:Task', 400, 120)
    const documentation = kit.moddle.create('bpmn:Documentation', { text: 'Beschreibung' })
    kit.modeling.updateProperties(task, { name: 'Prüfen', documentation: [documentation] })
    getBusinessObject(task).$attrs['flowaudit:marke'] = 'x'
    kit.modeling.setColor([task], { fill: '#c8e6c9' })
    kit.modeling.connect(kit.get('StartEvent_1'), task)
    const replaced = kit.replace.replaceElement(task, { type: 'bpmn:UserTask' })
    expect(replaced.id).toBe(task.id)
    const bo = getBusinessObject(replaced)
    expect(bo.$type).toBe('bpmn:UserTask')
    expect(bo.name).toBe('Prüfen')
    expect(bo.documentation?.[0]?.text).toBe('Beschreibung')
    expect(bo.$attrs['flowaudit:marke']).toBe('x')
    expect(replaced.di?.get('bioc:fill')).toBe('#c8e6c9')
    expect(replaced.incoming.length).toBe(1)
    kit.commandStack.undo()
    expect(getBusinessObject(kit.get(task.id)).$type).toBe('bpmn:Task')
  })

  it('ersetzt Ereignisse (Definitionen, unterbrechend) und Gateways', async () => {
    const kit = await createKit()
    const timer = kit.replace.replaceElement(kit.get('StartEvent_1'), { type: 'bpmn:StartEvent', eventDefinitionType: 'bpmn:TimerEventDefinition' })
    expect(getBusinessObject(timer).eventDefinitions?.[0]?.$type).toBe('bpmn:TimerEventDefinition')
    const end = kit.replace.replaceElement(timer, { type: 'bpmn:EndEvent', eventDefinitionType: 'bpmn:TerminateEventDefinition' })
    expect(end.type).toBe('bpmn:EndEvent')
    const eventBased = kit.replace.replaceElement(kit.create('bpmn:ExclusiveGateway', 400, 300), {
      type: 'bpmn:EventBasedGateway',
      eventGatewayType: 'Parallel',
      instantiate: true,
    })
    expect(getBusinessObject(eventBased).eventGatewayType).toBe('Parallel')
    expect(getBusinessObject(eventBased).instantiate).toBe(true)
  })

  it('bietet je Elementart passende Ziele ohne den aktuellen Zustand an', async () => {
    const kit = await createKit()
    const start = kit.get('StartEvent_1')
    const options = getReplaceOptions(start).map((option) => option.id)
    expect(options).not.toContain('replace-start-none')
    expect(options).toContain('replace-start-message')
    expect(getReplaceOptions(kit.create('bpmn:Task', 300, 300)).map((option) => option.id)).toContain('replace-user-task')
    expect(getReplaceOptions(kit.create('bpmn:ExclusiveGateway', 500, 300)).length).toBe(6)
  })

  it('heftet Zwischenereignis an und löst es wieder (Rand ↔ Zwischen)', async () => {
    const kit = await createKit()
    const task = kit.create('bpmn:Task', 400, 120)
    const event = kit.elementFactory.createShape({ type: 'bpmn:IntermediateThrowEvent' })
    const boundary = kit.modeling.createShape(event, { x: task.x + 50, y: task.y + task.height }, task as never, { attach: true })
    expect(boundary.type).toBe('bpmn:BoundaryEvent')
    expect(boundary.host).toBe(task)
    expect(getBusinessObject(boundary).attachedToRef).toBe(getBusinessObject(task))
    kit.modeling.moveElements([boundary], { x: 0, y: 200 }, kit.root() as never)
    const detached = kit.get(boundary.id)
    expect(detached.type).toBe('bpmn:IntermediateCatchEvent')
    expect(detached.host).toBeFalsy()
  })

  it('klappt Teilprozess auf und zu (Inhalt wandert in eigene Ebene)', async () => {
    const kit = await createKit()
    const sub = kit.create('bpmn:SubProcess', 500, 300, undefined, { isExpanded: true })
    expect(childrenOfType(sub, 'bpmn:StartEvent').length).toBe(1)
    const collapsed = kit.replace.replaceElement(sub, { type: 'bpmn:SubProcess', isExpanded: false })
    expect(collapsed.di?.isExpanded).toBe(false)
    expect(collapsed.width).toBe(100)
    const planeRoot = kit.get(`${collapsed.id}_plane`)
    expect(planeRoot.children.length).toBeGreaterThan(0)
    expect(await kit.xml()).toContain(`bpmnElement="${collapsed.id}"`)
    const expanded = kit.replace.replaceElement(collapsed, { type: 'bpmn:SubProcess', isExpanded: true })
    expect(childrenOfType(expanded, 'bpmn:StartEvent').length).toBe(1)
    expect(kit.registry.get(`${collapsed.id}_plane`)).toBeUndefined()
    kit.commandStack.undo()
    expect(kit.registry.get(`${collapsed.id}_plane`)).toBeTruthy()
  })

  it('wechselt zwischen Datenobjekt und Datenspeicher', async () => {
    const kit = await createKit()
    const data = kit.create('bpmn:DataObjectReference', 300, 300)
    const store = kit.replace.replaceElement(data, { type: 'bpmn:DataStoreReference' })
    expect(store.type).toBe('bpmn:DataStoreReference')
    const back = kit.replace.replaceElement(store, { type: 'bpmn:DataObjectReference' })
    expect(getBusinessObject(back).dataObjectRef).toBeTruthy()
  })
})
