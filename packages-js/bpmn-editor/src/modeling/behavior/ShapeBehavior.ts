/**
 * Formen:
 * - Neue aufgeklappte Teilprozesse erhalten ein Startereignis.
 * - Mindestgrößen und Kindgrenzen beim interaktiven Größenändern.
 */

import CommandInterceptor from 'diagram-js/lib/command/CommandInterceptor'

import { is, isExpanded } from '../../util/ModelUtil'
import { LANE_BAND, toBounds } from '../LaneUtil'
import type { BpmnElement, Bounds, CommandEvent, EventBus } from '../../types'
import type ElementFactory from '../ElementFactory'
import type Modeling from '../Modeling'

type Size = { width: number; height: number }

const MIN_SIZES: [string, Size][] = [
  ['bpmn:Participant', { width: 300, height: 60 }],
  ['bpmn:Lane', { width: 300, height: 60 }],
  ['bpmn:SubProcess', { width: 140, height: 120 }],
  ['bpmn:TextAnnotation', { width: 50, height: 30 }],
  ['bpmn:Group', { width: 60, height: 60 }],
  ['bpmn:Activity', { width: 60, height: 50 }],
]

interface CreateContext {
  shape?: BpmnElement
  elements?: BpmnElement[]
  hints?: { skipLabelCreation?: boolean; noStartEvent?: boolean; createElementsBehavior?: boolean }
}

interface ResizeStartContext {
  shape: BpmnElement
  minDimensions?: Size
  childrenBoxPadding?: number
  resizeConstraints?: { min: { top: number; left: number; bottom: number; right: number } }
}

function boundingBox(shapes: BpmnElement[]): Bounds {
  const boxes = shapes.map(toBounds)
  const x = Math.min(...boxes.map((box) => box.x))
  const y = Math.min(...boxes.map((box) => box.y))
  return {
    x,
    y,
    width: Math.max(...boxes.map((box) => box.x + box.width)) - x,
    height: Math.max(...boxes.map((box) => box.y + box.height)) - y,
  }
}

/** Pools dürfen nicht über ihren Inhalt hinweg verkleinert werden. */
function participantConstraints(shape: BpmnElement): ResizeStartContext['resizeConstraints'] {
  const nodes = ((shape.children || []) as BpmnElement[]).filter((child) => !is(child, 'bpmn:Lane') && !child.labelTarget && !child.waypoints)
  if (nodes.length === 0) return undefined
  const box = boundingBox(nodes)
  return {
    min: { top: box.y - 10, left: box.x - LANE_BAND - 10, bottom: box.y + box.height + 10, right: box.x + box.width + 10 },
  }
}

export default class ShapeBehavior extends CommandInterceptor {
  static $inject = ['eventBus', 'modeling', 'elementFactory']

  constructor(
    eventBus: EventBus,
    private readonly modeling: Modeling,
    private readonly elementFactory: ElementFactory,
  ) {
    super(eventBus)
    this.postExecute('shape.create', (event: CommandEvent<CreateContext>) => {
      const { context } = event
      if (context.hints?.skipLabelCreation || context.hints?.noStartEvent) return
      if (context.shape) this.addStartEvent(context.shape)
    })
    this.postExecute('elements.create', (event: CommandEvent<CreateContext>) => {
      const { context } = event
      if (context.hints?.noStartEvent || context.hints?.createElementsBehavior === false) return
      // Nur bei einzeln neu angelegten Teilprozessen (nicht beim Einfügen mit Inhalt).
      const shapes = (context.elements || []).filter((element) => !element.labelTarget && !element.waypoints)
      if (shapes.length === 1 && shapes[0]) this.addStartEvent(shapes[0])
    })
    eventBus.on('resize.start', 1500, (event: { context: ResizeStartContext }) => this.onResizeStart(event.context))
  }

  private addStartEvent(shape: BpmnElement): void {
    if (!is(shape, 'bpmn:SubProcess') || !isExpanded(shape) || !shape.parent) return
    if (((shape.children || []) as BpmnElement[]).some((child) => !child.labelTarget)) return
    const bounds = toBounds(shape)
    const start = this.elementFactory.createShape({ type: 'bpmn:StartEvent' })
    this.modeling.createShape(start as never, { x: bounds.x + 50, y: bounds.y + bounds.height / 2 }, shape as never)
  }

  private onResizeStart(context: ResizeStartContext): void {
    const shape = context.shape
    const entry = MIN_SIZES.find(([type]) => is(shape, type))
    if (entry) context.minDimensions = { ...entry[1] }
    if (is(shape, 'bpmn:Participant')) {
      const constraints = participantConstraints(shape)
      if (constraints) context.resizeConstraints = constraints
    }
    if (is(shape, 'bpmn:SubProcess')) context.childrenBoxPadding = 20
  }
}
