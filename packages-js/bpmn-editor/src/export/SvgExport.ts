/**
 * SVG-Export der aktiven Ebene: eigenständiges SVG mit Pfeilspitzen-
 * Definitionen und Rahmen um den Inhalt; Interaktionshilfen (Trefferflächen,
 * Umrisse, Auswahlrahmen) werden entfernt.
 */

/* eslint-disable @typescript-eslint/no-explicit-any */

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

export function computeContentBounds(elements: any[]): { x: number; y: number; width: number; height: number } {
  let minX = Infinity
  let minY = Infinity
  let maxX = -Infinity
  let maxY = -Infinity
  for (const element of elements) {
    if (element.waypoints) {
      for (const point of element.waypoints) {
        minX = Math.min(minX, point.x)
        minY = Math.min(minY, point.y)
        maxX = Math.max(maxX, point.x)
        maxY = Math.max(maxY, point.y)
      }
    } else if (typeof element.width === 'number') {
      minX = Math.min(minX, element.x)
      minY = Math.min(minY, element.y)
      maxX = Math.max(maxX, element.x + element.width)
      maxY = Math.max(maxY, element.y + element.height)
    }
  }
  if (!isFinite(minX)) return { x: 0, y: 0, width: 0, height: 0 }
  return { x: minX, y: minY, width: maxX - minX, height: maxY - minY }
}

export function exportSvg(canvas: any, elementRegistry: any, padding = 10): string {
  const layer: SVGGElement = canvas.getActiveLayer()
  const root = canvas.getRootElement()
  const clone = layer.cloneNode(true) as SVGGElement
  for (const selector of REMOVE_SELECTORS) {
    clone.querySelectorAll(selector).forEach((node) => node.parentNode?.removeChild(node))
  }
  const svgElement: SVGSVGElement = canvas._svg
  const defs = svgElement.querySelector('defs')
  const defsMarkup = defs ? new XMLSerializer().serializeToString(defs) : ''
  const content = Array.from(clone.childNodes)
    .map((node) => new XMLSerializer().serializeToString(node))
    .join('')
    .replace(/ xmlns="http:\/\/www\.w3\.org\/2000\/svg"/g, '')

  const elements = elementRegistry.filter((element: any) => element !== root && canvas.findRoot(element) === root)
  const bounds = computeContentBounds(elements)
  const x = Math.floor(bounds.x - padding)
  const y = Math.floor(bounds.y - padding)
  const width = Math.ceil(bounds.width + padding * 2)
  const height = Math.ceil(bounds.height + padding * 2)
  const cleanDefs = defsMarkup.replace(/ xmlns="http:\/\/www\.w3\.org\/2000\/svg"/g, '')

  return (
    '<?xml version="1.0" encoding="utf-8"?>\n' +
    '<!-- erstellt mit @flowaudit/bpmn-editor -->\n' +
    `<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" ` +
    `width="${width}" height="${height}" viewBox="${x} ${y} ${width} ${height}" version="1.1">` +
    cleanDefs +
    content +
    '</svg>'
  )
}
