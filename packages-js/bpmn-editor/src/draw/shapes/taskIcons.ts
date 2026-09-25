/**
 * Aufgabentyp-Symbole oben links in der Aufgabe.
 */

import * as G from '../Glyphs'
import { svgCircle, svgPath, type SvgAttrs } from '../svg'
import { getBusinessObject, is } from '../../util/ModelUtil'
import type { DrawContext } from './context'

const ORIGIN = 7

type IconDrawer = (parent: SVGElement, line: SvgAttrs, context: DrawContext) => void

const TASK_ICONS: [string, IconDrawer][] = [
  [
    'bpmn:UserTask',
    (parent, line) => {
      const icon = G.userIcon(ORIGIN, ORIGIN)
      svgPath(parent, icon.body, line)
      svgCircle(parent, icon.head.cx, icon.head.cy, icon.head.r, line)
    },
  ],
  ['bpmn:ManualTask', (parent, line) => void svgPath(parent, G.manualIcon(ORIGIN, ORIGIN), line)],
  [
    'bpmn:ServiceTask',
    (parent, line) => {
      const icon = G.serviceIcon(ORIGIN, ORIGIN)
      icon.gears.forEach((gear) => svgPath(parent, gear, line))
      icon.holes.forEach((hole) => svgCircle(parent, hole.cx, hole.cy, hole.r, line))
    },
  ],
  [
    'bpmn:ScriptTask',
    (parent, line) => {
      const icon = G.scriptIcon(ORIGIN, ORIGIN)
      svgPath(parent, icon.sheet, line)
      svgPath(parent, icon.lines, { ...line, fill: 'none' })
    },
  ],
  [
    'bpmn:BusinessRuleTask',
    (parent, line, context) => {
      const icon = G.businessRuleIcon(ORIGIN, ORIGIN)
      svgPath(parent, icon.table, line)
      svgPath(parent, icon.header, { ...line, fill: context.stroke, 'fill-opacity': 0.35 })
      svgPath(parent, icon.lines, { ...line, fill: 'none' })
    },
  ],
  [
    'bpmn:SendTask',
    (parent, line, context) => {
      const icon = G.messageTaskIcon(ORIGIN, ORIGIN)
      svgPath(parent, icon.body, { ...line, fill: context.stroke })
      svgPath(parent, icon.flap, { fill: 'none', stroke: context.fill, 'stroke-width': 1.1 })
    },
  ],
  [
    'bpmn:ReceiveTask',
    (parent, line, context) => {
      if (getBusinessObject(context.element).instantiate) svgCircle(parent, ORIGIN + 10, ORIGIN + 8, 9, { ...line, fill: 'none' })
      const icon = G.messageTaskIcon(ORIGIN, ORIGIN)
      svgPath(parent, icon.body, line)
      svgPath(parent, icon.flap, { fill: 'none', stroke: context.stroke, 'stroke-width': 1.1 })
    },
  ],
]

export function drawTaskIcon(parent: SVGElement, context: DrawContext): void {
  const entry = TASK_ICONS.find(([type]) => is(context.element, type))
  if (!entry) return
  entry[1](parent, { fill: context.fill, stroke: context.stroke, 'stroke-width': 1.1, 'stroke-linejoin': 'round' }, context)
}
