/**
 * Externe Beschriftungen:
 * - Beim Anlegen eines benannten Elements (z. B. beim Einfügen) entsteht
 *   die Beschriftung mit.
 * - Namensänderungen über `updateProperties` legen Beschriftungen an,
 *   passen sie an oder entfernen sie.
 * - Beschriftungen von Kanten folgen dem Kantenverlauf.
 */

import CommandInterceptor from 'diagram-js/lib/command/CommandInterceptor'

import {
  getExternalLabelBounds,
  getExternalLabelMid,
  getExternalLabelSize,
  getLabel,
  isLabelExternal,
} from '../../util/LabelUtil'
import { getBusinessObject, is } from '../../util/ModelUtil'

/* eslint-disable @typescript-eslint/no-explicit-any */

type Point = { x: number; y: number }

function pathMid(points: Point[]): Point {
  if (!points || points.length === 0) return { x: 0, y: 0 }
  let total = 0
  for (let i = 1; i < points.length; i++) total += Math.hypot(points[i].x - points[i - 1].x, points[i].y - points[i - 1].y)
  let remaining = total / 2
  for (let i = 1; i < points.length; i++) {
    const length = Math.hypot(points[i].x - points[i - 1].x, points[i].y - points[i - 1].y)
    if (remaining <= length && length > 0) {
      const ratio = remaining / length
      return { x: points[i - 1].x + (points[i].x - points[i - 1].x) * ratio, y: points[i - 1].y + (points[i].y - points[i - 1].y) * ratio }
    }
    remaining -= length
  }
  return points[0]
}

export default class LabelBehavior extends (CommandInterceptor as any) {
  static $inject = ['eventBus', 'modeling']

  constructor(eventBus: any, modeling: any) {
    super(eventBus)


    const ensureLabel = (element: any) => {
      if (!element || element.labelTarget || !element.parent) return
      if (!isLabelExternal(element)) return
      const text = getLabel(element)
      const label = element.label
      if (text && !label) {
        const di = element.di
        const bounds = di && di.label && di.label.bounds ? getExternalLabelBounds(di, element) : null
        const size = bounds ? { width: bounds.width, height: bounds.height } : getExternalLabelSize(text)
        let center: Point
        if (bounds) {
          center = { x: bounds.x + bounds.width / 2, y: bounds.y + bounds.height / 2 }
        } else {
          const mid = getExternalLabelMid(element)
          center = { x: mid.x, y: mid.y - 10 + size.height / 2 }
        }
        modeling.createLabel(element, center, {
          id: `${element.id}_label`,
          businessObject: element.businessObject,
          di: element.di,
          width: size.width,
          height: size.height,
        })
      } else if (label && !text) {
        modeling.removeShape(label)
      } else if (label && text) {
        const size = getExternalLabelSize(text)
        const centerX = label.x + label.width / 2
        const bounds = { x: Math.round(centerX - size.width / 2), y: label.y, width: size.width, height: size.height }
        if (bounds.x !== label.x || bounds.width !== label.width || bounds.height !== label.height) {
          modeling.resizeShape(label, bounds, { width: 0, height: 0 })
        }
      }
    }

    // Beim Einfügen mehrerer Elemente kommen Beschriftungen ggf. mit; erst danach ergänzen.
    this.preExecute('elements.create', 2000, (event: any) => {
      const context = event.context
      context.hints = { ...(context.hints || {}), skipLabelCreation: true }
    })
    this.postExecute('elements.create', (event: any) => {
      for (const element of event.context.elements || []) {
        if (!element.labelTarget) ensureLabel(element)
      }
    })

    this.postExecute(['shape.create', 'connection.create'], (event: any) => {
      const context = event.context
      const element = context.shape || context.connection
      if (context.hints && context.hints.skipLabelCreation) return
      if (element && !element.labelTarget) ensureLabel(element)
    })

    this.postExecute(['element.updateProperties', 'element.updateModdleProperties'], (event: any) => {
      const context = event.context
      const element = context.element
      const properties = context.properties || {}
      const bo = getBusinessObject(element)
      const relevant =
        'name' in properties ||
        'text' in properties ||
        'value' in properties ||
        'categoryValueRef' in properties ||
        (context.moddleElement && context.moddleElement !== bo && is(bo, 'bpmn:Group'))
      if (!relevant) return
      ensureLabel(element.labelTarget || element)
    })

    // Kantenbeschriftung wandert mit dem Mittelpunkt der Kante.
    this.postExecute(['connection.layout', 'connection.updateWaypoints', 'connection.reconnect'], (event: any) => {
      const context = event.context
      const connection = context.connection
      const label = connection && connection.label
      const hints = context.hints || {}
      if (!label || hints.labelBehavior === false) return
      const oldWaypoints: Point[] | undefined = context.oldWaypoints
      if (!oldWaypoints || !oldWaypoints.length) return
      const before = pathMid(oldWaypoints)
      const after = pathMid(connection.waypoints)
      const delta = { x: Math.round(after.x - before.x), y: Math.round(after.y - before.y) }
      if (delta.x || delta.y) modeling.moveShape(label, delta)
    })
  }
}
