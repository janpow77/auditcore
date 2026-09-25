/**
 * SVG building blocks for the export post-processing: plain shapes and
 * `<text>` only, so the result looks the same in Word, LibreOffice and the
 * browser.
 */

export const SVG_NS = 'http://www.w3.org/2000/svg'
export const FONT = "'Segoe UI', Frutiger, 'Helvetica Neue', Arial, sans-serif"
export const LINE_HEIGHT = 18

export interface TextOptions {
  size?: number
  bold?: boolean
  color?: string
  anchor?: 'start' | 'middle' | 'end'
}

export function svgText(doc: Document, x: number, y: number, content: string, options: TextOptions = {}): SVGTextElement {
  const text = doc.createElementNS(SVG_NS, 'text')
  text.setAttribute('x', String(x))
  text.setAttribute('y', String(y))
  text.setAttribute('font-family', FONT)
  text.setAttribute('font-size', String(options.size ?? 12))
  text.setAttribute('fill', options.color ?? '#111827')
  if (options.bold) text.setAttribute('font-weight', 'bold')
  if (options.anchor) text.setAttribute('text-anchor', options.anchor)
  text.textContent = content
  return text
}

export function svgRect(doc: Document, attrs: Record<string, string | number>): SVGRectElement {
  const rect = doc.createElementNS(SVG_NS, 'rect')
  for (const [name, value] of Object.entries(attrs)) rect.setAttribute(name, String(value))
  return rect
}

export function svgGroup(doc: Document): SVGGElement {
  return doc.createElementNS(SVG_NS, 'g')
}

/** Rough word wrap to a number of characters (SVG has no text measure). */
export function wrapWords(text: string, charsPerLine: number): string[] {
  const lines: string[] = []
  let current = ''
  for (const word of text.split(/\s+/).filter(Boolean)) {
    const candidate = current ? `${current} ${word}` : word
    if (candidate.length > charsPerLine && current) {
      lines.push(current)
      current = word
    } else {
      current = candidate
    }
  }
  if (current) lines.push(current)
  return lines.length ? lines : ['']
}

/** A block of the footer area with its height. */
export interface FooterBlock {
  group: SVGGElement
  height: number
}
