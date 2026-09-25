/**
 * Daten: Datenobjekt (auch Sammlung), Dateneingang/-ausgang, Datenspeicher.
 */

import * as G from '../Glyphs'
import { getBusinessObject, is } from '../../util/ModelUtil'
import { svgPath } from '../svg'
import { size, type DrawContext } from './context'

export function drawDataObject(parent: SVGElement, context: DrawContext): SVGElement {
  const { width, height } = size(context)
  const { fill, stroke } = context
  const fold = Math.min(10, width / 3)
  const line = { stroke, 'stroke-width': 1.5, 'stroke-linejoin': 'round' }
  const main = svgPath(parent, `M 0 0 L ${width - fold} 0 L ${width} ${fold} L ${width} ${height} L 0 ${height} Z`, { fill, ...line })
  svgPath(parent, `M ${width - fold} 0 L ${width - fold} ${fold} L ${width} ${fold}`, { fill: 'none', ...line })
  const bo = getBusinessObject(context.element)
  if (is(bo, 'bpmn:DataInput') || is(bo, 'bpmn:DataOutput')) {
    svgPath(parent, G.dataArrowPath(4, 4), {
      fill: is(bo, 'bpmn:DataOutput') ? stroke : fill,
      stroke,
      'stroke-width': 1,
      'stroke-linejoin': 'round',
    })
  }
  const dataObject = bo.dataObjectRef || bo
  if (dataObject && dataObject.isCollection) {
    svgPath(parent, G.collectionMarker(width / 2, height), { fill: 'none', stroke, 'stroke-width': 2 })
  }
  return main
}

export function drawDataStore(parent: SVGElement, context: DrawContext): SVGElement {
  const { width, height } = size(context)
  const ry = Math.min(7, height / 7)
  const rx = width / 2
  const main = svgPath(
    parent,
    `M 0 ${ry} A ${rx} ${ry} 0 0 1 ${width} ${ry} L ${width} ${height - ry} A ${rx} ${ry} 0 0 1 0 ${height - ry} Z`,
    { fill: context.fill, stroke: context.stroke, 'stroke-width': 1.5 },
  )
  const arcs = [ry, ry * 2, ry * 3].map((y) => `M 0 ${y} A ${rx} ${ry} 0 0 0 ${width} ${y}`).join(' ')
  svgPath(parent, arcs, { fill: 'none', stroke: context.stroke, 'stroke-width': 1.5 })
  return main
}
