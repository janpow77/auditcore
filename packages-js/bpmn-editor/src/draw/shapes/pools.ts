/**
 * Pools (Participant) und Bahnen (Lane), waagerecht oder senkrecht.
 */

import * as G from '../Glyphs'
import { getLabel } from '../../util/LabelUtil'
import { getBusinessObject, isExpanded, isHorizontal } from '../../util/ModelUtil'
import { attr, svgPath, svgRect, svgText } from '../svg'
import { hasCustomFill } from '../colors'
import { size, type DrawContext } from './context'

export const LANE_LABEL_BAND = 30

/** Senkrecht gesetzte Beschriftung im linken Kopfband. */
function drawRotatedLabel(parent: SVGElement, text: string | undefined, height: number, color: string): void {
  const element = svgText(
    parent,
    text,
    { box: { width: height, height: LANE_LABEL_BAND }, align: 'center-middle', padding: { left: 5, right: 5 } },
    color,
  )
  if (element) attr(element, { transform: `rotate(-90) translate(${-height}, 0)` })
}

function drawBand(parent: SVGElement, context: DrawContext, strokeWidth: number): void {
  const { width, height } = size(context)
  const text = getLabel(context.element)
  if (isHorizontal(context.element)) {
    svgPath(parent, `M ${LANE_LABEL_BAND} 0 L ${LANE_LABEL_BAND} ${height}`, { fill: 'none', stroke: context.stroke, 'stroke-width': strokeWidth })
    drawRotatedLabel(parent, text, height, context.labelColor)
  } else {
    svgPath(parent, `M 0 ${LANE_LABEL_BAND} L ${width} ${LANE_LABEL_BAND}`, { fill: 'none', stroke: context.stroke, 'stroke-width': strokeWidth })
    svgText(parent, text, { box: { width, height: LANE_LABEL_BAND }, align: 'center-middle', padding: 4 }, context.labelColor)
  }
}

export function drawParticipant(parent: SVGElement, context: DrawContext): SVGElement {
  const { width, height } = size(context)
  const main = svgRect(parent, width, height, 0, { fill: context.fill, stroke: context.stroke, 'stroke-width': 1.8 })
  if (isExpanded(context.element)) {
    drawBand(parent, context, 1.8)
  } else {
    svgText(parent, getLabel(context.element), { box: { width, height }, align: 'center-middle', padding: 5 }, context.labelColor)
  }
  if (getBusinessObject(context.element).participantMultiplicity) {
    svgPath(parent, G.collectionMarker(width / 2, height), { fill: 'none', stroke: context.stroke, 'stroke-width': 2 })
  }
  return main
}

export function drawLane(parent: SVGElement, context: DrawContext): SVGElement {
  const { width, height } = size(context)
  const main = svgRect(parent, width, height, 0, {
    fill: context.fill,
    'fill-opacity': hasCustomFill(context.element) ? 1 : 0.35,
    stroke: context.stroke,
    'stroke-width': 1.3,
  })
  drawBand(parent, context, 1.3)
  return main
}
