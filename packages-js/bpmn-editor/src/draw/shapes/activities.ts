/**
 * Aktivitäten: Aufgaben, Aufrufaktivität und Teilprozesse (aufgeklappt,
 * zugeklappt, Ereignis-Teilprozess, Transaktion, Ad-hoc).
 */

import { getLabel } from '../../util/LabelUtil'
import { getBusinessObject, is, isEventSubProcess, isExpanded } from '../../util/ModelUtil'
import { svgRect, svgText } from '../svg'
import { drawActivityMarkers } from './activityMarkers'
import { size, type DrawContext } from './context'
import { drawTaskIcon } from './taskIcons'

export const TASK_BORDER_RADIUS = 10

function drawCenteredLabel(parent: SVGElement, context: DrawContext, bottomPadding: number): void {
  const { width, height } = size(context)
  svgText(
    parent,
    getLabel(context.element),
    { box: { width, height }, align: 'center-middle', padding: { top: 5, bottom: bottomPadding, left: 5, right: 5 } },
    context.labelColor,
  )
}

function drawActivityFrame(parent: SVGElement, context: DrawContext, strokeWidth: number): SVGElement {
  const { width, height } = size(context)
  return svgRect(parent, width, height, TASK_BORDER_RADIUS, { fill: context.fill, stroke: context.stroke, 'stroke-width': strokeWidth })
}

export function drawTask(parent: SVGElement, context: DrawContext): SVGElement {
  const main = drawActivityFrame(parent, context, 2)
  drawTaskIcon(parent, context)
  drawCenteredLabel(parent, context, 5)
  drawActivityMarkers(parent, context, false)
  return main
}

export function drawCallActivity(parent: SVGElement, context: DrawContext): SVGElement {
  const main = drawActivityFrame(parent, context, 4.5)
  drawCenteredLabel(parent, context, 18)
  drawActivityMarkers(parent, context, false)
  return main
}

export function drawSubProcess(parent: SVGElement, context: DrawContext): SVGElement {
  const { width, height } = size(context)
  const expanded = isExpanded(context.element)
  const eventSub = isEventSubProcess(context.element)
  const main = svgRect(parent, width, height, TASK_BORDER_RADIUS, {
    fill: context.fill,
    stroke: context.stroke,
    'stroke-width': 2,
    'stroke-dasharray': eventSub ? '1.5,3' : undefined,
    'stroke-linecap': eventSub ? 'round' : undefined,
  })
  if (is(getBusinessObject(context.element), 'bpmn:Transaction')) {
    svgRect(parent, width, height, TASK_BORDER_RADIUS - 3, { fill: 'none', stroke: context.stroke, 'stroke-width': 1.5 }, 3)
  }
  if (expanded) {
    svgText(
      parent,
      getLabel(context.element),
      { box: { width, height }, align: 'left-top', padding: { top: 6, left: 10, right: 10 } },
      context.labelColor,
    )
  } else {
    drawCenteredLabel(parent, context, 18)
  }
  drawActivityMarkers(parent, context, !expanded)
  return main
}
