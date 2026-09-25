import { describe, expect, it } from 'vitest'

import { getBusinessObject } from '../src'
import { childrenOfType, createKit } from './helpers/modeling'

describe('Pools und Bahnen', () => {
  it('erster Pool umschließt den Prozess und macht eine Kollaboration', async () => {
    const kit = await createKit()
    const process = getBusinessObject(kit.root())
    const participant = kit.create('bpmn:Participant', 400, 200, undefined, { isExpanded: true })
    expect(getBusinessObject(kit.root()).$type).toBe('bpmn:Collaboration')
    expect(getBusinessObject(participant).processRef).toBe(process)
    const start = kit.get('StartEvent_1')
    expect(start.parent).toBe(participant)
    expect(start.x).toBeGreaterThan(participant.x)
    const xml = await kit.xml()
    expect(xml).toContain('<bpmn:collaboration')
    expect(xml).toContain(`processRef="${process.id}"`)
    kit.commandStack.undo()
    expect(getBusinessObject(kit.root()).$type).toBe('bpmn:Process')
    expect(kit.get('StartEvent_1').parent).toBe(kit.root())
  })

  it('legt Bahnen an (oberhalb, unterhalb, geteilt) und pflegt flowNodeRef', async () => {
    const kit = await createKit()
    const participant = kit.create('bpmn:Participant', 400, 200, undefined, { isExpanded: true })
    const below = kit.modeling.addLane(participant, 'bottom')
    const [first, second] = childrenOfType(participant, 'bpmn:Lane')
    if (!first || !second) throw new Error('Bahnen fehlen')
    expect(participant.height).toBeGreaterThan(250)
    expect(first.y + first.height).toBe(second.y)
    expect(below).toBe(second)
    const start = kit.get('StartEvent_1')
    expect(getBusinessObject(first).flowNodeRef).toContain(getBusinessObject(start))
    kit.modeling.moveElements([start], { x: 0, y: second.y + 40 - start.y })
    expect(getBusinessObject(second).flowNodeRef).toContain(getBusinessObject(start))
    expect(getBusinessObject(first).flowNodeRef).not.toContain(getBusinessObject(start))
    expect(kit.modeling.splitLane(second, 3).length).toBe(3)
    expect(getBusinessObject(second).childLaneSet?.lanes?.length).toBe(3)
    const above = kit.modeling.addLane(first, 'top')
    expect(above.y + above.height).toBe(first.y)
    expect(participant.y).toBe(above.y)
    const xml = await kit.xml()
    expect(xml).toContain('<bpmn:childLaneSet')
    expect(xml).toContain('<bpmn:flowNodeRef>StartEvent_1</bpmn:flowNodeRef>')
  })

  it('verteilt Platz beim Löschen einer Bahn und passt Bahnen bei Poolgröße an', async () => {
    const kit = await createKit()
    const participant = kit.create('bpmn:Participant', 400, 200, undefined, { isExpanded: true })
    kit.modeling.splitLane(participant, 3)
    const [a, b, c] = childrenOfType(participant, 'bpmn:Lane')
    if (!a || !b || !c) throw new Error('Bahnen fehlen')
    kit.modeling.removeShape(b)
    expect(childrenOfType(participant, 'bpmn:Lane').length).toBe(2)
    expect(a.y + a.height).toBe(c.y)
    kit.modeling.resizeShape(participant, { x: participant.x, y: participant.y, width: participant.width + 100, height: participant.height + 60 })
    const lanes = childrenOfType(participant, 'bpmn:Lane')
    for (const lane of lanes) expect(lane.x + lane.width).toBe(participant.x + participant.width)
    const last = lanes[lanes.length - 1]
    expect(last && last.y + last.height).toBe(participant.y + participant.height)
  })

  it('ändert die Größe einer Bahn mit Nachbarn (lane.resize)', async () => {
    const kit = await createKit()
    const participant = kit.create('bpmn:Participant', 400, 200, undefined, { isExpanded: true })
    kit.modeling.splitLane(participant, 2)
    const [top, bottom] = childrenOfType(participant, 'bpmn:Lane')
    if (!top || !bottom) throw new Error('Bahnen fehlen')
    const oldBottom = bottom.y
    kit.modeling.resizeLane(top, { x: top.x, y: top.y, width: top.width, height: top.height + 30 })
    expect(bottom.y).toBe(oldBottom + 30)
    expect(top.y + top.height).toBe(bottom.y)
  })

  it('unterstützt senkrechte Pools mit Bahnen', async () => {
    const kit = await createKit()
    const participant = kit.create('bpmn:Participant', 400, 400, undefined, { isExpanded: true, isHorizontal: false })
    expect(participant.di?.isHorizontal).toBe(false)
    expect(participant.height).toBeGreaterThan(participant.width)
    kit.modeling.splitLane(participant, 2)
    const lanes = childrenOfType(participant, 'bpmn:Lane').sort((a, b) => a.x - b.x)
    expect(lanes.length).toBe(2)
    expect(lanes[0]?.di?.isHorizontal).toBe(false)
    expect((lanes[0]?.x ?? 0) + (lanes[0]?.width ?? 0)).toBe(lanes[1]?.x)
  })

  it('verbindet Pools per Nachrichtenfluss und wechselt Flussart beim Verschieben', async () => {
    const kit = await createKit()
    const poolA = kit.create('bpmn:Participant', 400, 200, undefined, { isExpanded: true })
    const poolB = kit.create('bpmn:Participant', 400, 600, undefined, { isExpanded: true })
    const taskB = kit.create('bpmn:Task', 400, 600, poolB)
    const message = kit.modeling.connect(taskB, kit.get('StartEvent_1'))
    expect(message.type).toBe('bpmn:MessageFlow')
    expect(getBusinessObject(kit.root()).messageFlows).toContain(getBusinessObject(message))
    expect(kit.modeling.connect(poolA, poolB).type).toBe('bpmn:MessageFlow')
    // Beim Verschieben in Pool A entfällt der Fluss zum Startereignis (keine
    // eingehenden Sequenzflüsse), der zur Aufgabe wird zum Sequenzfluss.
    const taskA = kit.create('bpmn:Task', 700, 200, poolA)
    kit.modeling.connect(taskB, taskA)
    kit.modeling.moveElements([taskB], { x: 150, y: poolA.y + 100 - taskB.y }, poolA as never)
    const [connection] = taskB.outgoing
    expect(taskB.outgoing.length).toBe(1)
    expect(connection?.type).toBe('bpmn:SequenceFlow')
    expect(connection?.target).toBe(taskA)
    expect(getBusinessObject(poolA).processRef?.flowElements).toContain(getBusinessObject(connection as never))
  })

  it('macht nach Löschen des letzten Pools wieder einen Prozess', async () => {
    const kit = await createKit()
    kit.modeling.removeShape(kit.create('bpmn:Participant', 400, 200, undefined, { isExpanded: true }))
    expect(getBusinessObject(kit.root()).$type).toBe('bpmn:Process')
    expect(await kit.xml()).not.toContain('<bpmn:collaboration')
  })

  it('ersetzt Pool durch leeren Pool', async () => {
    const kit = await createKit()
    const participant = kit.create('bpmn:Participant', 400, 200, undefined, { isExpanded: true })
    const empty = kit.replace.replaceElement(participant, { type: 'bpmn:Participant', isExpanded: false })
    expect(getBusinessObject(empty).processRef).toBeUndefined()
    expect(kit.registry.get('StartEvent_1')).toBeUndefined()
  })
})
