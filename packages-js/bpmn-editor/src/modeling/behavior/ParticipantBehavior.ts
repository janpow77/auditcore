/**
 * Pools:
 * - Der erste Pool in einem Prozessdiagramm macht daraus eine Kollaboration
 *   und umschließt den vorhandenen Inhalt (der bisherige Prozess wird
 *   zum Prozess des Pools).
 * - Wird der letzte Pool gelöscht, wird die Wurzel wieder ein Prozess.
 */

import CommandInterceptor from 'diagram-js/lib/command/CommandInterceptor'

import { getBusinessObject, is, isHorizontal } from '../../util/ModelUtil'
import { toBounds } from '../LaneUtil'
import type { BpmnElement, Bounds, Canvas, CommandEvent, EventBus, Point } from '../../types'
import type Modeling from '../Modeling'

const PADDING = { band: 50, end: 40, side: 30 }

interface CreateContext {
  shape?: BpmnElement
  elements?: BpmnElement[]
  parent?: BpmnElement
  position?: Point
  wrapChildren?: BpmnElement[]
}

function boundingBox(shapes: BpmnElement[]): Bounds {
  const boxes = shapes.map(toBounds)
  const minX = Math.min(...boxes.map((box) => box.x))
  const minY = Math.min(...boxes.map((box) => box.y))
  const maxX = Math.max(...boxes.map((box) => box.x + box.width))
  const maxY = Math.max(...boxes.map((box) => box.y + box.height))
  return { x: minX, y: minY, width: maxX - minX, height: maxY - minY }
}

/** Neue Lage des Pools, sodass er den vorhandenen Inhalt umschließt. */
function wrappingCenter(participant: BpmnElement, children: BpmnElement[]): Point | null {
  const shapes = children.filter((child) => !child.waypoints)
  if (shapes.length === 0) return null
  const box = boundingBox(shapes)
  const horizontal = isHorizontal(participant)
  const x = box.x - (horizontal ? PADDING.band : PADDING.side)
  const y = box.y - (horizontal ? PADDING.side : PADDING.band)
  const width = Math.max(box.width + PADDING.band + PADDING.end, participant.width as number)
  const height = Math.max(box.height + PADDING.side * 2, participant.height as number)
  participant.width = width
  participant.height = height
  return { x: x + width / 2, y: y + height / 2 }
}

function isProcessRoot(element: BpmnElement | undefined): element is BpmnElement {
  return !!element && !element.parent && is(element, 'bpmn:Process')
}

export default class ParticipantBehavior extends CommandInterceptor {
  static $inject = ['eventBus', 'modeling', 'canvas']

  constructor(
    eventBus: EventBus,
    private readonly modeling: Modeling,
    private readonly canvas: Canvas,
  ) {
    super(eventBus)
    this.preExecute('shape.create', 1500, (event: CommandEvent<CreateContext>) => {
      const { context } = event
      if (context.shape && is(context.shape, 'bpmn:Participant')) this.prepareFirstParticipant(context, context.shape)
    })
    this.preExecute('elements.create', 1500, (event: CommandEvent<CreateContext>) => {
      const { context } = event
      const shapes = (context.elements || []).filter((element) => !element.labelTarget && !element.waypoints)
      const [participant] = shapes
      if (shapes.length === 1 && participant && is(participant, 'bpmn:Participant')) this.prepareFirstParticipant(context, participant)
    })
    this.postExecute(['shape.create', 'elements.create'], (event: CommandEvent<CreateContext>) => this.wrap(event.context))
    this.postExecute('shape.delete', (event: CommandEvent<CreateContext>) => this.revertToProcess(event.context.shape))
  }

  /** Erster Pool: Prozess übernehmen, Wurzel zur Kollaboration machen. */
  private prepareFirstParticipant(context: CreateContext, participant: BpmnElement): void {
    const root = context.parent
    if (!isProcessRoot(root)) return
    getBusinessObject(participant).processRef = getBusinessObject(root)
    context.wrapChildren = ((root.children || []) as BpmnElement[]).slice()
    const center = wrappingCenter(participant, context.wrapChildren)
    if (center) context.position = center
    context.parent = this.modeling.makeCollaboration()
  }

  private wrap(context: CreateContext): void {
    const children = context.wrapChildren
    if (!children || children.length === 0) return
    const participant = context.shape || (context.elements || []).find((element) => is(element, 'bpmn:Participant'))
    const movable = children.filter((child) => !child.labelTarget && !child.host && child.parent)
    if (participant && movable.length) this.modeling.moveElements(movable as never, { x: 0, y: 0 }, participant as never, { autoResize: false } as never)
  }

  private revertToProcess(shape: BpmnElement | undefined): void {
    if (!shape || !is(shape, 'bpmn:Participant')) return
    const root = this.canvas.getRootElement() as unknown as BpmnElement
    if (!is(root, 'bpmn:Collaboration')) return
    const remaining = ((root.children || []) as BpmnElement[]).filter((child) => !child.labelTarget)
    if (remaining.length === 0) this.modeling.makeProcess()
  }
}
