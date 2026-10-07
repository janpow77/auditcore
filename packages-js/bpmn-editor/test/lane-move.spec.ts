import { describe, expect, it } from 'vitest'

import type { Shape } from 'diagram-js/lib/model/Types'
import { frameOf, replaceLanes } from '../src/lane-move/LaneMove'
import { childrenOfType, createKit } from './helpers/modeling'

interface StartContext {
  shape?: Shape
  shapes?: Shape[]
  validatedShapes?: Shape[]
}

async function poolWithLanes() {
  const kit = await createKit()
  const participant = kit.create('bpmn:Participant', 400, 200, undefined, { isExpanded: true })
  kit.modeling.addLane(participant, 'bottom')
  const lanes = childrenOfType(participant, 'bpmn:Lane')
  return { kit, participant: participant as unknown as Shape, lanes: lanes as unknown as Shape[] }
}

describe('Bahnen verschieben ihren Pool', () => {
  it('ersetzt eine Bahn durch ihren Pool', async () => {
    const { participant, lanes } = await poolWithLanes()
    expect(frameOf(lanes[0]!)).toBe(participant)
    expect(frameOf(participant)).toBe(participant)
  })

  it('führt Bahnen, Pool und Pool-Inhalt in einer Auswahl auf den Pool zurück', async () => {
    const { kit, participant, lanes } = await poolWithLanes()
    const start = kit.get('StartEvent_1') as unknown as Shape
    expect(replaceLanes([lanes[0]!, lanes[1]!, start])).toEqual([participant])
  })

  it('stellt den Verschiebe-Kontext beim Start auf den Pool um', async () => {
    const { kit, participant, lanes } = await poolWithLanes()
    const eventBus = kit.editor.get<{ fire: (type: string, event: unknown) => unknown }>('eventBus')
    const context: StartContext = {}
    eventBus.fire('shape.move.start', { shape: lanes[0], context })
    expect(context.shape).toBe(participant)
    expect(context.shapes).toEqual([participant])
    expect(context.validatedShapes).toEqual([participant])
  })

  it('lässt das Verschieben anderer Elemente unberührt', async () => {
    const { kit } = await poolWithLanes()
    const start = kit.get('StartEvent_1') as unknown as Shape
    const eventBus = kit.editor.get<{ fire: (type: string, event: unknown) => unknown }>('eventBus')
    const context: StartContext = {}
    eventBus.fire('shape.move.start', { shape: start, context })
    expect(context.shapes).toEqual([start])
  })
})
