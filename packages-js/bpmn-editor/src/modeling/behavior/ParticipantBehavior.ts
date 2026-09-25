/**
 * Pools:
 * - Der erste Pool in einem Prozessdiagramm macht daraus eine Kollaboration
 *   und umschließt den vorhandenen Inhalt (der bisherige Prozess wird
 *   zum Prozess des Pools).
 * - Wird der letzte Pool gelöscht, wird die Wurzel wieder ein Prozess.
 */

import CommandInterceptor from 'diagram-js/lib/command/CommandInterceptor'

import { getBusinessObject, is, isHorizontal } from '../../util/ModelUtil'

/* eslint-disable @typescript-eslint/no-explicit-any */

const PADDING = { left: 50, right: 40, top: 30, bottom: 30 }

export default class ParticipantBehavior extends (CommandInterceptor as any) {
  static $inject = ['eventBus', 'modeling', 'canvas', 'elementRegistry']

  constructor(eventBus: any, modeling: any, canvas: any, _elementRegistry: any) {
    super(eventBus)

    const wrapCreate = (context: any, shape: any) => {
      const parent = context.parent || context.target
      if (!shape || !is(shape, 'bpmn:Participant') || !parent || parent.parent) return
      if (!is(parent, 'bpmn:Process')) return
      const root = parent
      const processBo = getBusinessObject(root)
      const children = root.children.filter((child: any) => !child.labelTarget || true)

      // Der Pool übernimmt den vorhandenen Prozess.
      if (getBusinessObject(shape).processRef !== processBo) {
        getBusinessObject(shape).processRef = processBo
      }

      if (children.length > 0) {
        const shapes = children.filter((child: any) => !child.waypoints)
        const bbox = getBounds(shapes)
        const horizontal = isHorizontal(shape)
        const bounds = {
          x: bbox.x - (horizontal ? PADDING.left : PADDING.top),
          y: bbox.y - (horizontal ? PADDING.top : PADDING.left),
          width: bbox.width + PADDING.left + PADDING.right,
          height: bbox.height + PADDING.top + PADDING.bottom,
        }
        bounds.width = Math.max(bounds.width, shape.width)
        bounds.height = Math.max(bounds.height, shape.height)
        shape.width = bounds.width
        shape.height = bounds.height
        context.wrapChildren = children
        return { x: bounds.x + bounds.width / 2, y: bounds.y + bounds.height / 2 }
      }
      context.wrapChildren = []
      return null
    }

    this.preExecute('shape.create', 1500, (event: any) => {
      const context = event.context
      const shape = context.shape
      if (!is(shape, 'bpmn:Participant')) return
      const parent = context.parent
      if (!parent || parent.parent || !is(parent, 'bpmn:Process')) return
      const center = wrapCreate(context, shape)
      if (center) context.position = center
      const collaborationRoot = modeling.makeCollaboration()
      context.parent = collaborationRoot
    })

    this.postExecute('shape.create', (event: any) => {
      const context = event.context
      const children: any[] = context.wrapChildren
      if (!children || children.length === 0) return
      const movable = children.filter((child: any) => !child.labelTarget && !child.host && child.parent)
      if (movable.length) modeling.moveElements(movable, { x: 0, y: 0 }, context.shape, { autoResize: false })
    })

    // Mehrfaches Einfügen (Palette nutzt elements.create): gleiches Verhalten.
    this.preExecute('elements.create', 1500, (event: any) => {
      const context = event.context
      const elements: any[] = context.elements || []
      const participant = elements.find((element) => is(element, 'bpmn:Participant') && !element.parent)
      const parent = context.parent
      if (!participant || !parent || parent.parent || !is(parent, 'bpmn:Process')) return
      if (elements.filter((element) => !element.labelTarget && !element.waypoints).length !== 1) return
      const center = wrapCreate(context, participant)
      if (center) context.position = center
      context.parent = modeling.makeCollaboration()
    })

    this.postExecute('elements.create', (event: any) => {
      const context = event.context
      const children: any[] = context.wrapChildren
      if (!children || children.length === 0) return
      const participant = (context.elements || []).find((element: any) => is(element, 'bpmn:Participant'))
      const movable = children.filter((child: any) => !child.labelTarget && !child.host && child.parent)
      if (participant && movable.length) modeling.moveElements(movable, { x: 0, y: 0 }, participant, { autoResize: false })
    })

    // Letzter Pool gelöscht → Prozess
    this.postExecute('shape.delete', (event: any) => {
      const shape = event.context.shape
      if (!is(shape, 'bpmn:Participant')) return
      const root = canvas.getRootElement()
      if (!is(root, 'bpmn:Collaboration')) return
      const remaining = root.children.filter((child: any) => !child.labelTarget)
      if (remaining.length === 0) modeling.makeProcess()
    })
  }
}

function getBounds(shapes: any[]): { x: number; y: number; width: number; height: number } {
  let minX = Infinity
  let minY = Infinity
  let maxX = -Infinity
  let maxY = -Infinity
  for (const shape of shapes) {
    minX = Math.min(minX, shape.x)
    minY = Math.min(minY, shape.y)
    maxX = Math.max(maxX, shape.x + shape.width)
    maxY = Math.max(maxY, shape.y + shape.height)
  }
  return { x: minX, y: minY, width: maxX - minX, height: maxY - minY }
}
