import { describe, expect, it } from 'vitest'

import { canResize } from '../src/rules/resizeRules'
import { canDrop, isPointOnBorder } from '../src/rules/containmentRules'
import { readFixture } from './helpers/fixtures'
import { createKit, type Kit } from './helpers/modeling'

async function allElementsKit(): Promise<Kit> {
  return createKit(readFixture('synthetisch/alle-elemente.bpmn'))
}

describe('Verbindungsregeln', () => {
  it('Sequenzfluss nur innerhalb desselben Bereichs und nicht in Start- oder aus Endereignisse', async () => {
    const kit = await allElementsKit()
    expect(kit.rules.canConnect(kit.get('Task_Plain'), kit.get('Task_User'))).toEqual({ type: 'bpmn:SequenceFlow' })
    expect(kit.rules.canConnect(kit.get('Task_Plain'), kit.get('Start_None'))).toBe(false)
    expect(kit.rules.canConnect(kit.get('End_None'), kit.get('Task_Plain'))).toBe(false)
    expect(kit.rules.canConnect(kit.get('Task_Plain'), kit.get('Boundary_Timer'))).toBe(false)
    // In einen Teilprozess hinein ist kein Sequenzfluss erlaubt.
    expect(kit.rules.canConnect(kit.get('Task_Plain'), kit.get('Sub_Task'))).toBe(false)
    expect(kit.rules.canConnect(kit.get('Task_Plain'), kit.get('Task_Plain'))).toBe(false)
  })

  it('Nachrichtenfluss nur zwischen verschiedenen Pools', async () => {
    const kit = await allElementsKit()
    expect(kit.rules.canConnect(kit.get('Participant_B'), kit.get('Task_Receive'))).toEqual({ type: 'bpmn:MessageFlow' })
    expect(kit.rules.canConnect(kit.get('C_Task'), kit.get('Participant_B'))).toEqual({ type: 'bpmn:MessageFlow' })
    expect(kit.rules.canConnect(kit.get('Task_Send'), kit.get('Participant_B'))).toEqual({ type: 'bpmn:MessageFlow' })
    // Sendeaufgaben empfangen keine Nachrichten, Gateways nehmen nicht teil.
    expect(kit.rules.canConnect(kit.get('C_Task'), kit.get('Task_Send'))).toBe(false)
    expect(kit.rules.canConnect(kit.get('Participant_B'), kit.get('Gateway_X'))).toBe(false)
  })

  it('ereignisbasiertes Gateway nur zu fangenden Ereignissen bzw. Empfangsaufgaben', async () => {
    const kit = await allElementsKit()
    expect(kit.rules.canConnect(kit.get('Gateway_E'), kit.get('Catch_Timer'))).toEqual({ type: 'bpmn:SequenceFlow' })
    expect(kit.rules.canConnect(kit.get('Gateway_E'), kit.get('Task_Receive'))).toEqual({ type: 'bpmn:SequenceFlow' })
    expect(kit.rules.canConnect(kit.get('Gateway_E'), kit.get('Task_Plain'))).toBe(false)
  })

  it('Daten- und Textassoziationen', async () => {
    const kit = await allElementsKit()
    expect(kit.rules.canConnect(kit.get('DataRef_1'), kit.get('Task_Plain'))).toEqual({ type: 'bpmn:DataInputAssociation' })
    expect(kit.rules.canConnect(kit.get('Task_Plain'), kit.get('DataStore_1'))).toEqual({ type: 'bpmn:DataOutputAssociation' })
    expect(kit.rules.canConnect(kit.get('Task_Plain'), kit.get('DataInput_1'))).toBe(false)
    expect(kit.rules.canConnect(kit.get('Note_1'), kit.get('Task_Plain'))).toEqual({ type: 'bpmn:Association', associationDirection: 'None' })
    expect(kit.rules.canConnect(kit.get('Note_1'), kit.get('Sub_Note'))).toBe(false)
    expect(kit.rules.canConnect(kit.get('Boundary_Compensate'), kit.get('Task_Script'))).toEqual({
      type: 'bpmn:Association',
      associationDirection: 'One',
    })
  })

  it('prüft bestehende Kanten nach ihrem Typ', async () => {
    const kit = await allElementsKit()
    const flow = kit.get('Flow_1')
    expect(kit.rules.canConnect(kit.get('Start_None'), kit.get('Task_User'), flow)).toEqual({ type: 'bpmn:SequenceFlow' })
    expect(kit.rules.canConnect(kit.get('Participant_B'), kit.get('Task_User'), flow)).toBe(false)
  })
})

describe('Container-, Anheft- und Größenregeln', () => {
  it('Flussknoten nur in Prozesse, Pools, Bahnen und aufgeklappte Teilprozesse', async () => {
    const kit = await allElementsKit()
    const task = kit.elementFactory.createShape({ type: 'bpmn:Task' })
    expect(canDrop(task, kit.get('Participant_A'))).toBe(true)
    expect(canDrop(task, kit.get('Lane_Pruefung'))).toBe(true)
    expect(canDrop(task, kit.get('Sub_Expanded'))).toBe(true)
    expect(canDrop(task, kit.get('Sub_Collapsed'))).toBe(false)
    expect(canDrop(task, kit.get('Participant_B'))).toBe(false)
    expect(canDrop(task, kit.root())).toBe(false)
    const participant = kit.elementFactory.createShape({ type: 'bpmn:Participant' })
    expect(canDrop(participant, kit.root())).toBe(true)
    expect(canDrop(participant, kit.get('Participant_A'))).toBe(false)
    const note = kit.elementFactory.createShape({ type: 'bpmn:TextAnnotation' })
    expect(canDrop(note, kit.root())).toBe(true)
  })

  it('Randereignisse haften nur an Aktivitäten und nur am Rand', async () => {
    const kit = await allElementsKit()
    const event = kit.elementFactory.createShape({ type: 'bpmn:IntermediateThrowEvent' })
    const task = kit.get('Task_Plain')
    expect(kit.rules.canAttach([event], task, null, { x: task.x + 10, y: task.y + task.height })).toBe('attach')
    expect(kit.rules.canAttach([event], task, null, { x: task.x + 50, y: task.y + 40 })).toBe(false)
    expect(kit.rules.canAttach([event], kit.get('Gateway_X'), null)).toBe(false)
    expect(kit.rules.canAttach([kit.elementFactory.createShape({ type: 'bpmn:StartEvent' })], task, null)).toBe(false)
    expect(isPointOnBorder(task, { x: task.x, y: task.y + 10 })).toBe(true)
  })

  it('Bahnen werden nur mit ihrem Pool verschoben', async () => {
    const kit = await allElementsKit()
    expect(kit.rules.canMove([kit.get('Lane_Antrag')], kit.root())).toBe(false)
    expect(kit.rules.canMove([kit.get('Participant_A'), kit.get('Lane_Antrag')], kit.root())).toBe(true)
  })

  it('Größenänderung mit Mindestmaßen je Typ', async () => {
    const kit = await allElementsKit()
    const task = kit.get('Task_Plain')
    expect(canResize(task, { x: 0, y: 0, width: 120, height: 90 })).toBe(true)
    expect(canResize(task, { x: 0, y: 0, width: 20, height: 20 })).toBe(false)
    expect(canResize(kit.get('Start_None'))).toBe(false)
    expect(canResize(kit.get('Gateway_X'))).toBe(false)
    expect(canResize(kit.get('Participant_A'), { x: 0, y: 0, width: 400, height: 200 })).toBe(true)
    expect(canResize(kit.get('Sub_Expanded'), { x: 0, y: 0, width: 50, height: 50 })).toBe(false)
  })

  it('Ausrichten ignoriert Beschriftungen, Bahnen und Kanten', async () => {
    const kit = await allElementsKit()
    const rules = kit.editor.get<{ allowed(action: string, context: unknown): unknown }>('rules')
    const allowed = rules.allowed('elements.align', {
      elements: [kit.get('Task_Plain'), kit.get('Lane_Antrag'), kit.get('Flow_1'), kit.get('Task_User')],
    }) as unknown[]
    expect(allowed.map((element) => (element as { id: string }).id)).toEqual(['Task_Plain', 'Task_User'])
  })
})
