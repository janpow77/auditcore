/**
 * Aktivitätsmarker unten mittig: zugeklappt (+), Schleife, Mehrfachinstanz,
 * Kompensation, Ad-hoc.
 */

import * as G from '../Glyphs'
import { svgElement, svgPath, type SvgAttrs } from '../svg'
import { getBusinessObject, getLoopType, is } from '../../util/ModelUtil'
import { size, type DrawContext } from './context'

type Marker = 'collapsed' | 'loop' | 'parallel' | 'sequential' | 'compensation' | 'adhoc'

const MARKER_SIZE = 14
const MARKER_GAP = 4

type MarkerDrawer = (parent: SVGElement, cx: number, cy: number, line: SvgAttrs, context: DrawContext) => void

const MARKER_DRAWERS: Record<Marker, MarkerDrawer> = {
  collapsed: (parent, cx, cy, line, context) => {
    const icon = G.collapsedMarker(cx, cy)
    svgPath(parent, icon.frame, { fill: context.fill, stroke: context.stroke, 'stroke-width': 1.3 })
    svgPath(parent, icon.plus, line)
  },
  loop: (parent, cx, cy, line) => void svgPath(parent, G.loopMarker(cx, cy), line),
  parallel: (parent, cx, cy, line) => void svgPath(parent, G.parallelMarker(cx, cy), { ...line, 'stroke-width': 2 }),
  sequential: (parent, cx, cy, line) => void svgPath(parent, G.sequentialMarker(cx, cy), { ...line, 'stroke-width': 2 }),
  compensation: (parent, cx, cy, _line, context) =>
    void svgPath(parent, G.compensationMarker(cx, cy), { fill: context.fill, stroke: context.stroke, 'stroke-width': 1.2 }),
  adhoc: (parent, cx, cy, line) => void svgPath(parent, G.adHocMarker(cx, cy), { ...line, 'stroke-width': 1.6 }),
}

export function collectMarkers(context: DrawContext, collapsed: boolean): Marker[] {
  const bo = getBusinessObject(context.element)
  const markers: Marker[] = []
  if (collapsed) markers.push('collapsed')
  const loop = getLoopType(context.element)
  if (loop) markers.push(loop)
  if (bo.isForCompensation) markers.push('compensation')
  if (is(bo, 'bpmn:AdHocSubProcess')) markers.push('adhoc')
  return markers
}

export function drawActivityMarkers(parent: SVGElement, context: DrawContext, collapsed: boolean): void {
  const markers = collectMarkers(context, collapsed)
  if (markers.length === 0) return
  const { width, height } = size(context)
  const total = markers.length * MARKER_SIZE + (markers.length - 1) * MARKER_GAP
  let cx = width / 2 - total / 2 + MARKER_SIZE / 2
  const cy = height - 4 - MARKER_SIZE / 2
  const line = { fill: 'none', stroke: context.stroke, 'stroke-width': 1.5, 'stroke-linecap': 'round' }
  for (const marker of markers) {
    const group = svgElement(parent, 'g', { class: `fa-marker fa-marker-${marker}` })
    MARKER_DRAWERS[marker](group, cx, cy, line, context)
    cx += MARKER_SIZE + MARKER_GAP
  }
}
