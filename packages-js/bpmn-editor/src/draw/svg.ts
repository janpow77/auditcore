/**
 * Kleine SVG-Hilfen für die Renderer.
 */

import { append, attr, create } from 'tiny-svg'

import { createTextElement, type TextBoxOptions } from './TextLayout'

export type SvgAttrs = Record<string, string | number | undefined | null>

function clean(attrs: SvgAttrs): Record<string, string | number> {
  const result: Record<string, string | number> = {}
  for (const [key, value] of Object.entries(attrs)) {
    if (value !== undefined && value !== null) result[key] = value
  }
  return result
}

/** Erzeugt ein SVG-Element, setzt Attribute und hängt es an `parent` an. */
export function svgElement(parent: SVGElement, tag: string, attrs: SvgAttrs): SVGElement {
  const element = create(tag) as SVGElement
  attr(element, clean(attrs))
  append(parent, element)
  return element
}

export function svgPath(parent: SVGElement, d: string, attrs: SvgAttrs): SVGElement {
  return svgElement(parent, 'path', { d, ...attrs })
}

export function svgCircle(parent: SVGElement, cx: number, cy: number, r: number, attrs: SvgAttrs): SVGElement {
  return svgElement(parent, 'circle', { cx, cy, r: Math.max(0, r), ...attrs })
}

/** Rechteck mit optionalem Einzug (`inset`) und abgerundeten Ecken. */
export function svgRect(parent: SVGElement, width: number, height: number, radius: number, attrs: SvgAttrs, inset = 0): SVGElement {
  return svgElement(parent, 'rect', {
    x: inset,
    y: inset,
    width: Math.max(0, width - inset * 2),
    height: Math.max(0, height - inset * 2),
    rx: radius,
    ry: radius,
    ...attrs,
  })
}

/** Text in einer Box; liefert `null`, wenn kein Text vorliegt. */
export function svgText(parent: SVGElement, text: string | undefined, options: TextBoxOptions, color: string): SVGElement | null {
  if (!text) return null
  const element = createTextElement(text, options)
  attr(element, { fill: color })
  append(parent, element)
  return element
}

export { append, attr, create }
