import { describe, expect, it } from 'vitest'

import { getBusinessObject } from '../src'
import type { CreatedElement, ModdleElement } from '../src/types'
import { createKit } from './helpers/modeling'

describe('Modellierung: Anlegen, Verbinden, Verschieben, Löschen', () => {
  it('legt Aufgabe an und verbindet mit Sequenzfluss (semantisch und DI)', async () => {
    const kit = await createKit()
    const start = kit.get('StartEvent_1')
    const task = kit.create('bpmn:Task', 400, 120)
    const flow = kit.modeling.connect(start, task)
    expect(flow.type).toBe('bpmn:SequenceFlow')
    const bo = getBusinessObject(flow)
    expect(bo.sourceRef).toBe(getBusinessObject(start))
    expect(bo.targetRef).toBe(getBusinessObject(task))
    expect(getBusinessObject(start).outgoing).toContain(bo)
    expect(getBusinessObject(task).incoming).toContain(bo)
    const process = getBusinessObject(kit.root())
    expect(process.flowElements).toContain(bo)
    expect(process.flowElements).toContain(getBusinessObject(task))
    const xml = await kit.xml()
    expect(xml).toContain(`<bpmn:sequenceFlow id="${bo.id}" sourceRef="StartEvent_1" targetRef="${task.id}"`)
    expect(xml).toContain(`<bpmndi:BPMNEdge id="${bo.id}_di" bpmnElement="${bo.id}">`)
    expect(flow.waypoints.length).toBeGreaterThanOrEqual(2)
  })

  it('führt Sequenzflüsse rechtwinklig und schneidet am Umriss ab', async () => {
    const kit = await createKit()
    const gateway = kit.create('bpmn:ExclusiveGateway', 400, 120)
    const task = kit.create('bpmn:Task', 600, 300)
    const flow = kit.modeling.connect(gateway, task)
    const points = flow.waypoints as { x: number; y: number }[]
    for (let i = 1; i < points.length; i++) {
      const a = points[i - 1]
      const b = points[i]
      expect(a && b && (a.x === b.x || a.y === b.y)).toBe(true)
    }
    expect(points[0]).toMatchObject({ x: 400 })
    expect(points[points.length - 1]).toMatchObject({ x: 550 })
  })

  it('verschiebt, ändert Größe und löscht mit Rückgängig/Wiederholen', async () => {
    const kit = await createKit()
    const task = kit.create('bpmn:Task', 400, 120)
    kit.modeling.moveShape(task, { x: 30, y: 40 })
    expect(task.di?.bounds?.x).toBe(task.x)
    expect(task.di?.bounds?.y).toBe(task.y)
    kit.modeling.resizeShape(task, { x: task.x, y: task.y, width: 160, height: 90 })
    expect(task.di?.bounds?.width).toBe(160)
    kit.modeling.removeShape(task)
    expect(kit.registry.get(task.id)).toBeUndefined()
    expect(getBusinessObject(kit.root()).flowElements).not.toContain(getBusinessObject(task))
    kit.commandStack.undo()
    expect(kit.registry.get(task.id)).toBe(task)
    expect(getBusinessObject(kit.root()).flowElements).toContain(getBusinessObject(task))
    expect(task.di?.$parent?.planeElement).toContain(task.di)
    kit.commandStack.undo()
    expect(task.di?.bounds?.width).toBe(100)
    kit.commandStack.redo()
    kit.commandStack.redo()
    expect(kit.registry.get(task.id)).toBeUndefined()
  })

  it('verbindet Vorgänger und Nachfolger beim Löschen eines Zwischenschritts', async () => {
    const kit = await createKit()
    const start = kit.get('StartEvent_1')
    const task = kit.create('bpmn:Task', 400, 120)
    const end = kit.create('bpmn:EndEvent', 600, 120)
    const first = kit.modeling.connect(start, task)
    kit.modeling.connect(task, end)
    kit.modeling.removeShape(task)
    expect(first.target).toBe(end)
    expect(getBusinessObject(first).targetRef).toBe(getBusinessObject(end))
  })

  it('pflegt Standardfluss und bedingten Fluss', async () => {
    const kit = await createKit()
    const gateway = kit.create('bpmn:ExclusiveGateway', 400, 120)
    const toA = kit.modeling.connect(gateway, kit.create('bpmn:Task', 600, 60))
    const toB = kit.modeling.connect(gateway, kit.create('bpmn:Task', 600, 220))
    kit.replace.replaceFlow(toA, 'default')
    expect(getBusinessObject(gateway).default).toBe(getBusinessObject(toA))
    kit.replace.replaceFlow(toB, 'conditional')
    expect(getBusinessObject(toB).conditionExpression?.$type).toBe('bpmn:FormalExpression')
    kit.replace.replaceFlow(toB, 'sequence')
    expect(getBusinessObject(toB).conditionExpression).toBeUndefined()
    kit.modeling.removeConnection(toA)
    expect(getBusinessObject(gateway).default).toBeUndefined()
    kit.commandStack.undo()
    expect(getBusinessObject(gateway).default).toBe(getBusinessObject(toA))
  })

  it('setzt und entfernt Farben (bioc und color)', async () => {
    const kit = await createKit()
    const start = kit.get('StartEvent_1')
    kit.modeling.setColor([start], { fill: '#ffcdd2', stroke: '#b71c1c' })
    expect(start.di?.get('bioc:fill')).toBe('#ffcdd2')
    expect(start.di?.get('color:background-color')).toBe('#ffcdd2')
    expect(start.di?.get('color:border-color')).toBe('#b71c1c')
    expect(await kit.xml()).toContain('bioc:stroke="#b71c1c"')
    kit.modeling.setColor([start], { fill: null, stroke: null })
    expect(start.di?.get('bioc:fill')).toBeUndefined()
    kit.commandStack.undo()
    expect(start.di?.get('bioc:fill')).toBe('#ffcdd2')
  })

  it('ändert Eigenschaften und moddle-Eigenschaften (auch Kennung)', async () => {
    const kit = await createKit()
    const task = kit.create('bpmn:Task', 400, 120)
    const originalId = task.id
    kit.modeling.updateProperties(task, { name: 'Prüfen', id: 'Task_Pruefen' })
    expect(kit.registry.get('Task_Pruefen')).toBe(task)
    expect(task.di?.id).toBe('Task_Pruefen_di')
    const extension = kit.moddle.create('bpmn:ExtensionElements')
    kit.modeling.updateModdleProperties(task, getBusinessObject(task), { extensionElements: extension })
    kit.modeling.updateModdleProperties(task, task.di as ModdleElement, { 'bioc:fill': '#eeeeee' })
    expect(task.di?.get('bioc:fill')).toBe('#eeeeee')
    kit.commandStack.undo()
    kit.commandStack.undo()
    kit.commandStack.undo()
    expect(kit.registry.get(originalId)).toBe(task)
    expect(getBusinessObject(task).name).toBeUndefined()
  })

  it('meldet Änderungen über die Ereignisse commandStack.changed und element.changed', async () => {
    const kit = await createKit()
    const seen: string[] = []
    kit.editor.on('commandStack.changed', () => seen.push('commandStack'))
    kit.editor.on('element.changed', () => seen.push('element'))
    kit.modeling.updateProperties(kit.get('StartEvent_1'), { name: 'Los' })
    expect(seen).toContain('commandStack')
    expect(seen).toContain('element')
  })
})

describe('Modellierung: Beschriftungen und Artefakte', () => {
  it('legt externe Beschriftungen an, ändert und entfernt sie', async () => {
    const kit = await createKit()
    const start = kit.get('StartEvent_1')
    kit.modeling.updateLabel(start, 'Antrag eingegangen')
    expect(start.label).toBeTruthy()
    expect(start.di?.label?.bounds?.y).toBeGreaterThan(start.y + start.height - 1)
    kit.modeling.moveShape(start.label as CreatedElement, { x: 10, y: 10 })
    expect(start.di?.label?.bounds?.x).toBe(start.label?.x)
    kit.modeling.updateLabel(start, '')
    expect(start.label).toBeFalsy()
    expect(getBusinessObject(start).name).toBeUndefined()
    kit.commandStack.undo()
    expect(start.label).toBeTruthy()
  })

  it('legt Beschriftung auch über updateProperties an und lässt Kantenbeschriftung mitwandern', async () => {
    const kit = await createKit()
    const gateway = kit.create('bpmn:ExclusiveGateway', 300, 120)
    kit.modeling.updateProperties(gateway, { name: 'Vollständig?' })
    expect(gateway.label).toBeTruthy()
    const task = kit.create('bpmn:Task', 500, 120)
    const flow = kit.modeling.connect(gateway, task)
    kit.modeling.updateLabel(flow, 'ja')
    const before = flow.label?.x
    kit.modeling.moveElements([task], { x: 100, y: 0 })
    expect(flow.label?.x).toBeGreaterThan(before ?? 0)
  })

  it('beschriftet Textanmerkung und Gruppe', async () => {
    const kit = await createKit()
    const note = kit.create('bpmn:TextAnnotation', 400, 300)
    kit.modeling.updateLabel(note, 'Hinweis')
    expect(getBusinessObject(note).text).toBe('Hinweis')
    const group = kit.create('bpmn:Group', 700, 400)
    kit.modeling.updateLabel(group, 'Phase 1')
    expect(getBusinessObject(group).categoryValueRef?.value).toBe('Phase 1')
    expect(await kit.xml()).toMatch(/<bpmn:category id="[^"]+">\s*<bpmn:categoryValue id="[^"]+" value="Phase 1"/)
  })

  it('verbindet Textanmerkung per Assoziation und Daten per Datenassoziation', async () => {
    const kit = await createKit()
    const task = kit.create('bpmn:Task', 400, 120)
    const association = kit.modeling.connect(kit.create('bpmn:TextAnnotation', 400, 300), task)
    expect(association.type).toBe('bpmn:Association')
    const input = kit.modeling.connect(kit.create('bpmn:DataObjectReference', 250, 300), task)
    expect(input.type).toBe('bpmn:DataInputAssociation')
    expect(getBusinessObject(task).dataInputAssociations).toContain(getBusinessObject(input))
    const store = kit.create('bpmn:DataStoreReference', 600, 300)
    const output = kit.modeling.connect(task, store)
    expect(output.type).toBe('bpmn:DataOutputAssociation')
    expect(getBusinessObject(output).targetRef).toBe(getBusinessObject(store))
    const xml = await kit.xml()
    expect(xml).toContain('<bpmn:dataInputAssociation')
    expect(xml).toContain('<bpmn:dataObject id=')
    kit.modeling.removeConnection(input)
    expect(getBusinessObject(task).dataInputAssociations).not.toContain(getBusinessObject(input))
  })

  it('legt Dateneingang und -ausgang in der ioSpecification des Prozesses an', async () => {
    const kit = await createKit()
    kit.create('bpmn:DataInput', 300, 300)
    kit.create('bpmn:DataOutput', 400, 300)
    const io = getBusinessObject(kit.root()).ioSpecification
    expect(io?.get<ModdleElement[]>('dataInputs').length).toBe(1)
    expect(io?.get<ModdleElement[]>('dataOutputs').length).toBe(1)
    expect(io?.get<ModdleElement[]>('inputSets').length).toBe(1)
  })
})

describe('Modellierung: Ausrichten, Verteilen, Raumwerkzeug', () => {
  it('richtet aus und verteilt', async () => {
    const kit = await createKit()
    const a = kit.create('bpmn:Task', 300, 100)
    const b = kit.create('bpmn:Task', 500, 180)
    const c = kit.create('bpmn:Task', 900, 260)
    kit.editor.get<{ trigger(elements: unknown[], type: string): void }>('alignElements').trigger([a, b, c], 'top')
    expect(b.y).toBe(a.y)
    expect(c.y).toBe(a.y)
    kit.editor.get<{ trigger(elements: unknown[], type: string): void }>('distributeElements').trigger([a, b, c], 'horizontal')
    expect(Math.abs(b.x - a.x - (c.x - b.x))).toBeLessThanOrEqual(1)
  })

  it('schafft Platz mit dem Raumwerkzeug', async () => {
    const kit = await createKit()
    const task = kit.create('bpmn:Task', 400, 120)
    const oldX = task.x
    kit.modeling.createSpace([task], [], { x: 100, y: 0 }, 'e', 300)
    expect(task.x).toBe(oldX + 100)
    expect(task.di?.bounds?.x).toBe(oldX + 100)
  })
})
