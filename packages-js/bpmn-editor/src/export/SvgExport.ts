/**
 * SVG-Export der aktiven Ebene: eigenständiges SVG mit Pfeilspitzen-
 * Definitionen und Rahmen um den Inhalt; Interaktionshilfen (Trefferflächen,
 * Umrisse, Auswahlrahmen) werden entfernt.
 */

import type { Element } from 'diagram-js/lib/model/Types'

import type { Bounds, Canvas, ElementRegistry, Point } from '../types'

const REMOVE_SELECTORS = [
  '.djs-hit',
  '.djs-outline',
  '.djs-bendpoints',
  '.djs-segment-dragger',
  '.djs-bendpoint',
  '.djs-connection-preview',
  '.djs-dragger',
  '.djs-resizer',
  '.djs-drag-group',
]

function cornerPoints(element: Element): Point[] {
  if (element.waypoints) return element.waypoints as Point[]
  if (typeof element.width !== 'number') return []
  const box = element as unknown as Bounds
  return [
    { x: box.x, y: box.y },
    { x: box.x + box.width, y: box.y + box.height },
  ]
}

/** Umschließendes Rechteck einer Menge von Formen und Kanten. */
export function computeContentBounds(elements: Element[]): Bounds {
  const points = elements.flatMap(cornerPoints)
  if (points.length === 0) return { x: 0, y: 0, width: 0, height: 0 }
  const xs = points.map((point) => point.x)
  const ys = points.map((point) => point.y)
  const x = Math.min(...xs)
  const y = Math.min(...ys)
  return { x, y, width: Math.max(...xs) - x, height: Math.max(...ys) - y }
}

function serialize(node: Node): string {
  return new XMLSerializer().serializeToString(node).replace(/ xmlns="http:\/\/www\.w3\.org\/2000\/svg"/g, '')
}

export function exportSvg(canvas: Canvas, elementRegistry: ElementRegistry, padding = 10): string {
  const layer = canvas.getActiveLayer() as unknown as SVGGElement
  const root = canvas.getRootElement()
  const clone = layer.cloneNode(true) as SVGGElement
  for (const selector of REMOVE_SELECTORS) clone.querySelectorAll(selector).forEach((node) => node.remove())
  const svgElement = (canvas as unknown as { _svg: SVGSVGElement })._svg
  const defs = Array.from(svgElement.children).find((child) => child.localName === 'defs')
  const content = Array.from(clone.childNodes).map(serialize).join('')
  const elements = elementRegistry.filter((element) => element !== root && canvas.findRoot(element as never) === root)
  const bounds = computeContentBounds(elements)
  const x = Math.floor(bounds.x - padding)
  const y = Math.floor(bounds.y - padding)
  const width = Math.ceil(bounds.width + padding * 2)
  const height = Math.ceil(bounds.height + padding * 2)
  return (
    '<?xml version="1.0" encoding="utf-8"?>\n' +
    '<!-- erstellt mit @flowaudit/bpmn-editor -->\n' +
    `<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" ` +
    `width="${width}" height="${height}" viewBox="${x} ${y} ${width} ${height}" version="1.1">` +
    (defs ? serialize(defs) : '') +
    content +
    '</svg>'
  )
}
