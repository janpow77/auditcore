/**
 * Ereignisse: Kreis(e) je Ereignisart und Symbol der Ereignisdefinition.
 */

import * as G from '../Glyphs'
import { svgCircle, svgPath, type SvgAttrs } from '../svg'
import { getBusinessObject, getEventDefinitions, is, isAny, isInterrupting } from '../../util/ModelUtil'
import type { ModdleElement } from '../../types'
import { size, type DrawContext } from './context'

interface GlyphArgs {
  parent: SVGElement
  cx: number
  cy: number
  s: number
  base: SvgAttrs
  fill: string
  stroke: string
  lineColor: string
}

type GlyphDrawer = (args: GlyphArgs) => void

/** Symbol je Ereignisdefinition (deklarative Tabelle). */
const DEFINITION_GLYPHS: [string, GlyphDrawer][] = [
  [
    'bpmn:MessageEventDefinition',
    ({ parent, cx, cy, s, base, lineColor }) => {
      const envelope = G.envelopePaths(cx, cy, s)
      svgPath(parent, envelope.body, base)
      svgPath(parent, envelope.flap, { fill: 'none', stroke: lineColor, 'stroke-width': 1.2 })
    },
  ],
  [
    'bpmn:TimerEventDefinition',
    ({ parent, cx, cy, s, fill, stroke }) => {
      svgCircle(parent, cx, cy, 10 * s, { fill, stroke, 'stroke-width': 1.5 })
      svgPath(parent, G.timerTicks(cx, cy, s), { fill: 'none', stroke, 'stroke-width': 1 })
      svgPath(parent, G.timerHands(cx, cy, s), { fill: 'none', stroke, 'stroke-width': 1.5, 'stroke-linecap': 'round' })
    },
  ],
  ['bpmn:EscalationEventDefinition', ({ parent, cx, cy, s, base }) => void svgPath(parent, G.escalationPath(cx, cy, s), base)],
  [
    'bpmn:ConditionalEventDefinition',
    ({ parent, cx, cy, s, base, fill, stroke }) => {
      const icon = G.conditionalPaths(cx, cy, s)
      svgPath(parent, icon.sheet, { ...base, fill })
      svgPath(parent, icon.lines, { fill: 'none', stroke, 'stroke-width': 1.2 })
    },
  ],
  ['bpmn:LinkEventDefinition', ({ parent, cx, cy, s, base }) => void svgPath(parent, G.linkPath(cx, cy, s), base)],
  ['bpmn:ErrorEventDefinition', ({ parent, cx, cy, s, base }) => void svgPath(parent, G.errorPath(cx, cy, s), base)],
  ['bpmn:CancelEventDefinition', ({ parent, cx, cy, s, base }) => void svgPath(parent, G.cancelPath(cx, cy, s), base)],
  ['bpmn:CompensateEventDefinition', ({ parent, cx, cy, s, base }) => void svgPath(parent, G.compensationPath(cx - 0.5 * s, cy, s), base)],
  ['bpmn:SignalEventDefinition', ({ parent, cx, cy, s, base }) => void svgPath(parent, G.signalPath(cx, cy, s), base)],
  [
    'bpmn:TerminateEventDefinition',
    ({ parent, cx, cy, s, stroke }) => void svgCircle(parent, cx, cy, 10.5 * s, { fill: stroke, stroke, 'stroke-width': 1 }),
  ],
]

function drawDefinitions(parent: SVGElement, context: DrawContext, cx: number, cy: number, s: number, isThrow: boolean): void {
  const definitions: ModdleElement[] = getEventDefinitions(context.element)
  if (definitions.length === 0) return
  const { fill, stroke } = context
  const args: GlyphArgs = {
    parent,
    cx,
    cy,
    s,
    fill,
    stroke,
    lineColor: isThrow ? fill : stroke,
    base: { fill: isThrow ? stroke : fill, stroke, 'stroke-width': 1.2, 'stroke-linejoin': 'round' },
  }
  if (definitions.length > 1) {
    if (getBusinessObject(context.element).parallelMultiple) svgPath(parent, G.parallelMultiplePath(cx, cy, s), { ...args.base, fill })
    else svgPath(parent, G.multiplePath(cx, cy, s), args.base)
    return
  }
  const definition = definitions[0]
  const entry = DEFINITION_GLYPHS.find(([type]) => !!definition && is(definition, type))
  entry?.[1](args)
}

export function drawEvent(parent: SVGElement, context: DrawContext): SVGElement {
  const { fill, stroke, element } = context
  const { width, height } = size(context)
  const cx = width / 2
  const cy = height / 2
  const radius = Math.min(width, height) / 2
  const s = radius / 18
  const bo = getBusinessObject(element)
  let main: SVGElement
  if (is(bo, 'bpmn:StartEvent')) {
    main = svgCircle(parent, cx, cy, radius, {
      fill,
      stroke,
      'stroke-width': 2,
      'stroke-dasharray': isInterrupting(element) ? undefined : '6,3.5',
    })
  } else if (is(bo, 'bpmn:EndEvent')) {
    main = svgCircle(parent, cx, cy, radius, { fill, stroke, 'stroke-width': 4 })
  } else {
    const dashed = is(bo, 'bpmn:BoundaryEvent') && !isInterrupting(element) ? '5.5,3' : undefined
    main = svgCircle(parent, cx, cy, radius, { fill, stroke, 'stroke-width': 1.5, 'stroke-dasharray': dashed })
    svgCircle(parent, cx, cy, radius - 3 * s, { fill: 'none', stroke, 'stroke-width': 1.5, 'stroke-dasharray': dashed })
  }
  drawDefinitions(parent, context, cx, cy, s, isAny(bo, ['bpmn:EndEvent', 'bpmn:IntermediateThrowEvent']))
  return main
}
