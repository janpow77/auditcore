/**
 * Artefakte (Textanmerkung, Gruppe) und externe Beschriftungen.
 */

import { getLabel, EXTERNAL_LABEL_FONT_SIZE } from '../../util/LabelUtil'
import { hasCustomFill } from '../colors'
import { svgElement, svgPath, svgRect, svgText } from '../svg'
import { size, type DrawContext } from './context'
import { TASK_BORDER_RADIUS } from './activities'

export function drawTextAnnotation(parent: SVGElement, context: DrawContext): SVGElement {
  const { width, height } = size(context)
  const main = svgRect(parent, width, height, 0, {
    fill: hasCustomFill(context.element) ? context.fill : 'none',
    stroke: 'none',
  })
  svgPath(parent, `M 10 0 L 0 0 L 0 ${height} L 10 ${height}`, { fill: 'none', stroke: context.stroke, 'stroke-width': 1.5 })
  svgText(parent, getLabel(context.element), { box: { width, height }, align: 'left-top', padding: 5 }, context.labelColor)
  return main
}

export function drawGroup(parent: SVGElement, context: DrawContext): SVGElement {
  const { width, height } = size(context)
  return svgRect(parent, width, height, TASK_BORDER_RADIUS, {
    fill: 'none',
    stroke: context.stroke,
    'stroke-width': 1.5,
    'stroke-dasharray': '10,4,2,4',
  })
}

export function drawLabel(parent: SVGElement, context: DrawContext): SVGElement {
  const { width, height } = size(context)
  const group = svgElement(parent, 'g', {})
  const text = svgText(
    group,
    getLabel(context.element) || ' ',
    { box: { width, height }, align: 'center-top', style: { fontSize: EXTERNAL_LABEL_FONT_SIZE } },
    context.labelColor,
  )
  return text || group
}
