/**
 * Formen:
 * - Neue aufgeklappte Teilprozesse erhalten ein Startereignis.
 * - Mindestgrößen und Kindgrenzen beim interaktiven Größenändern.
 */

import CommandInterceptor from 'diagram-js/lib/command/CommandInterceptor'

import { is, isExpanded } from '../../util/ModelUtil'
import { LANE_BAND } from '../LaneUtil'

/* eslint-disable @typescript-eslint/no-explicit-any */

const MIN_SIZES: [string, { width: number; height: number }][] = [
  ['bpmn:Participant', { width: 300, height: 60 }],
  ['bpmn:Lane', { width: 300, height: 60 }],
  ['bpmn:SubProcess', { width: 140, height: 120 }],
  ['bpmn:TextAnnotation', { width: 50, height: 30 }],
  ['bpmn:Group', { width: 60, height: 60 }],
  ['bpmn:Activity', { width: 60, height: 50 }],
]

export default class ShapeBehavior extends (CommandInterceptor as any) {
  static $inject = ['eventBus', 'modeling', 'elementFactory']

  constructor(eventBus: any, modeling: any, elementFactory: any) {
    super(eventBus)

    const addStartEvent = (shape: any) => {
      if (!is(shape, 'bpmn:SubProcess') || !isExpanded(shape) || !shape.parent) return
      if ((shape.children || []).some((child: any) => !child.labelTarget)) return
      const start = elementFactory.createShape({ type: 'bpmn:StartEvent' })
      modeling.createShape(start, { x: shape.x + 50, y: shape.y + shape.height / 2 }, shape)
    }

    this.postExecute('shape.create', (event: any) => {
      const context = event.context
      if (context.hints && context.hints.skipLabelCreation) return
      if (context.hints && context.hints.noStartEvent) return
      addStartEvent(context.shape)
    })
    this.postExecute('elements.create', (event: any) => {
      const context = event.context
      const elements: any[] = context.elements || []
      if (context.hints && context.hints.noStartEvent) return
      // Nur bei einzeln neu angelegten Teilprozessen (nicht beim Einfügen mit Inhalt).
      const shapes = elements.filter((element) => !element.labelTarget && !element.waypoints)
      if (shapes.length === 1) addStartEvent(shapes[0])
    })

    eventBus.on('resize.start', 1500, (event: any) => {
      const context = event.context
      const shape = context.shape
      for (const [type, size] of MIN_SIZES) {
        if (is(shape, type)) {
          context.minDimensions = { ...size }
          break
        }
      }
      if (is(shape, 'bpmn:Participant')) {
        const nodes = (shape.children || []).filter((child: any) => !is(child, 'bpmn:Lane') && !child.labelTarget && !child.waypoints)
        if (nodes.length) {
          const box = bbox(nodes)
          context.resizeConstraints = {
            min: {
              top: box.y - 10,
              left: box.x - LANE_BAND - 10,
              bottom: box.y + box.height + 10,
              right: box.x + box.width + 10,
            },
          }
        }
      }
      if (is(shape, 'bpmn:SubProcess')) context.childrenBoxPadding = 20
    })
  }
}

function bbox(shapes: any[]) {
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
