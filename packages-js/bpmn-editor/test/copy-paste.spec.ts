import { describe, expect, it } from 'vitest'

import { getBusinessObject } from '../src'
import type { BpmnElement } from '../src/types'
import { createKit, type Kit } from './helpers/modeling'

interface CopyPaste {
  copy(elements: BpmnElement[]): unknown
  paste(context: { element: BpmnElement; point: { x: number; y: number } }): BpmnElement[]
}

function copyPaste(kit: Kit): CopyPaste {
  return kit.editor.get<CopyPaste>('copyPaste')
}

async function sourceKit(): Promise<{ kit: Kit; task: BpmnElement; gateway: BpmnElement; flow: BpmnElement }> {
  const kit = await createKit()
  const task = kit.create('bpmn:UserTask', 300, 300)
  kit.modeling.updateProperties(task, { name: 'Antrag prüfen' })
  const definitions = kit.editor.getDefinitions()
  if (definitions) definitions.$attrs['xmlns:flowaudit'] = 'https://flowaudit.de/bpmn/schema/1.0'
  getBusinessObject(task).$attrs['flowaudit:marke'] = 'ja'
  kit.modeling.setColor([task], { fill: '#dbeafe', stroke: '#1d4ed8' })
  const gateway = kit.create('bpmn:ExclusiveGateway', 500, 300)
  kit.modeling.updateLabel(gateway, 'Vollständig?')
  const flow = kit.modeling.connect(task, gateway) as BpmnElement
  kit.modeling.updateProperties(task, { default: getBusinessObject(flow) })
  return { kit, task, gateway, flow }
}

describe('Kopieren und Einfügen', () => {
  it('fügt innerhalb eines Diagramms mit neuen Kennungen ein', async () => {
    const { kit, task, gateway, flow } = await sourceKit()
    copyPaste(kit).copy([task, gateway, flow])
    const pasted = copyPaste(kit).paste({ element: kit.root(), point: { x: 400, y: 600 } })
    const newTask = pasted.find((element) => element.type === 'bpmn:UserTask') as BpmnElement
    const newFlow = pasted.find((element) => element.type === 'bpmn:SequenceFlow') as BpmnElement
    expect(newTask.id).not.toBe(task.id)
    expect(getBusinessObject(newTask).name).toBe('Antrag prüfen')
    expect(getBusinessObject(newTask).$attrs['flowaudit:marke']).toBe('ja')
    expect(newTask.di?.get('bioc:fill')).toBe('#dbeafe')
    expect(getBusinessObject(newTask).default).toBe(getBusinessObject(newFlow))
    const newGateway = pasted.find((element) => element.type === 'bpmn:ExclusiveGateway') as BpmnElement
    expect(newGateway.label).toBeTruthy()
    expect(pasted.filter((element) => element.labelTarget).length).toBe(1)
    expect(getBusinessObject(kit.root()).flowElements?.length).toBe(7)
  })

  it('fügt zwischen zwei Editoren ein (gemeinsame Zwischenablage)', async () => {
    const { kit, task, gateway, flow } = await sourceKit()
    copyPaste(kit).copy([task, gateway, flow])
    const target = await createKit()
    const pasted = copyPaste(target).paste({ element: target.root(), point: { x: 400, y: 400 } })
    expect(pasted.length).toBeGreaterThanOrEqual(3)
    const xml = await target.xml()
    expect(xml).toContain('name="Antrag prüfen"')
    expect(xml).toContain('flowaudit:marke="ja"')
    const newTask = pasted.find((element) => element.type === 'bpmn:UserTask') as BpmnElement
    expect(getBusinessObject(newTask).$parent).toBe(getBusinessObject(target.root()))
  })

  it('kopiert Datenobjekte und Gruppen mit eigenen Begleitobjekten', async () => {
    const kit = await createKit()
    const data = kit.create('bpmn:DataObjectReference', 300, 300)
    const group = kit.create('bpmn:Group', 600, 400)
    kit.modeling.updateLabel(group, 'Phase 1')
    copyPaste(kit).copy([data, group])
    const pasted = copyPaste(kit).paste({ element: kit.root(), point: { x: 300, y: 700 } })
    const newData = pasted.find((element) => element.type === 'bpmn:DataObjectReference') as BpmnElement
    const newGroup = pasted.find((element) => element.type === 'bpmn:Group') as BpmnElement
    expect(getBusinessObject(newData).dataObjectRef).not.toBe(getBusinessObject(data).dataObjectRef)
    expect(getBusinessObject(newGroup).categoryValueRef?.value).toBe('Phase 1')
    expect(getBusinessObject(newGroup).categoryValueRef).not.toBe(getBusinessObject(group).categoryValueRef)
  })

  it('Einfügen ist rückgängig machbar', async () => {
    const { kit, task } = await sourceKit()
    copyPaste(kit).copy([task])
    const before = kit.registry.getAll().length
    copyPaste(kit).paste({ element: kit.root(), point: { x: 800, y: 600 } })
    expect(kit.registry.getAll().length).toBeGreaterThan(before)
    kit.commandStack.undo()
    expect(kit.registry.getAll().length).toBe(before)
  })
})
