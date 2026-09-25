/**
 * Gateways: Raute und Markierung je Gateway-Art.
 */

import * as G from '../Glyphs'
import { svgCircle, svgElement, svgPath } from '../svg'
import { getBusinessObject, getDi, is } from '../../util/ModelUtil'
import type { ModdleElement } from '../../types'
import { size, type DrawContext } from './context'

type MarkerDrawer = (parent: SVGElement, cx: number, cy: number, s: number, context: DrawContext) => void

function eventBasedMarker(parent: SVGElement, cx: number, cy: number, s: number, context: DrawContext): void {
  const bo = getBusinessObject(context.element)
  const line = { fill: 'none', stroke: context.stroke, 'stroke-width': 1.3 }
  svgCircle(parent, cx, cy, 12.5 * s, line)
  if (bo.eventGatewayType === 'Parallel') {
    svgPath(parent, G.crossPath(cx, cy, 2.4 * s, 7.5 * s), { ...line, fill: context.fill })
    return
  }
  if (!bo.instantiate) svgCircle(parent, cx, cy, 10 * s, line)
  svgPath(parent, G.regularPolygonPath(cx, cy + 0.5 * s, 6.5 * s, 5), line)
}

const GATEWAY_MARKERS: [string, MarkerDrawer][] = [
  [
    'bpmn:ExclusiveGateway',
    (parent, cx, cy, s, context) => {
      const di = getDi(context.element) as ModdleElement | undefined
      if (di && di.isMarkerVisible) {
        svgPath(parent, G.crossPath(cx, cy, 2.6 * s, 11 * s, Math.PI / 4), { fill: context.stroke, stroke: context.stroke, 'stroke-width': 1 })
      }
    },
  ],
  [
    'bpmn:ParallelGateway',
    (parent, cx, cy, s, context) =>
      void svgPath(parent, G.crossPath(cx, cy, 2.6 * s, 13 * s), { fill: context.stroke, stroke: context.stroke, 'stroke-width': 1 }),
  ],
  [
    'bpmn:InclusiveGateway',
    (parent, cx, cy, s, context) => void svgCircle(parent, cx, cy, 11 * s, { fill: 'none', stroke: context.stroke, 'stroke-width': 2.6 }),
  ],
  [
    'bpmn:ComplexGateway',
    (parent, cx, cy, s, context) => {
      const filled = { fill: context.stroke, stroke: context.stroke, 'stroke-width': 1 }
      svgPath(parent, G.crossPath(cx, cy, 2 * s, 12.5 * s), filled)
      svgPath(parent, G.crossPath(cx, cy, 2 * s, 11 * s, Math.PI / 4), filled)
    },
  ],
  ['bpmn:EventBasedGateway', eventBasedMarker],
]

export function drawGateway(parent: SVGElement, context: DrawContext): SVGElement {
  const { width, height } = size(context)
  const cx = width / 2
  const cy = height / 2
  const main = svgElement(parent, 'polygon', {
    points: `${cx},0 ${width},${cy} ${cx},${height} 0,${cy}`,
    fill: context.fill,
    stroke: context.stroke,
    'stroke-width': 2,
    'stroke-linejoin': 'round',
  })
  const entry = GATEWAY_MARKERS.find(([type]) => is(context.element, type))
  entry?.[1](parent, cx, cy, Math.min(width, height) / 50, context)
  return main
}
