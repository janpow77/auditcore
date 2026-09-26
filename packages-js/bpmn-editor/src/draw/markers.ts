/**
 * Pfeilspitzen und Anfangsmarken der Kanten (SVG-`<marker>`), je Farbkombi-
 * nation einmal in den `<defs>` der Zeichenfläche angelegt.
 */

import { svgElement, type SvgAttrs } from './svg'

export type MarkerType =
  | 'sequence-end'
  | 'message-end'
  | 'message-start'
  | 'association-end'
  | 'association-start'
  | 'conditional-start'
  | 'default-start'

interface MarkerSpec {
  ref: { x: number; y: number }
  shape: (fill: string, stroke: string) => { tag: string; attrs: SvgAttrs }
}

const MARKERS: Record<MarkerType, MarkerSpec> = {
  'sequence-end': {
    ref: { x: 11, y: 10 },
    shape: (_fill, stroke) => ({ tag: 'path', attrs: { d: 'M 1 5 L 11 10 L 1 15 Z', fill: stroke, stroke, 'stroke-width': 1, 'stroke-linejoin': 'round' } }),
  },
  'message-end': {
    ref: { x: 11, y: 10 },
    shape: (fill, stroke) => ({ tag: 'path', attrs: { d: 'M 1 5 L 11 10 L 1 15 Z', fill, stroke, 'stroke-width': 1, 'stroke-linejoin': 'round' } }),
  },
  'message-start': {
    ref: { x: 6, y: 10 },
    shape: (fill, stroke) => ({ tag: 'circle', attrs: { cx: 6, cy: 10, r: 3.5, fill, stroke, 'stroke-width': 1 } }),
  },
  'association-end': {
    ref: { x: 11, y: 10 },
    shape: (_fill, stroke) => ({ tag: 'path', attrs: { d: 'M 1 4.5 L 11 10 L 1 15.5', fill: 'none', stroke, 'stroke-width': 1.5, 'stroke-linecap': 'round' } }),
  },
  'association-start': {
    ref: { x: 1, y: 10 },
    shape: (_fill, stroke) => ({ tag: 'path', attrs: { d: 'M 11 4.5 L 1 10 L 11 15.5', fill: 'none', stroke, 'stroke-width': 1.5, 'stroke-linecap': 'round' } }),
  },
  'conditional-start': {
    ref: { x: -1, y: 10 },
    shape: (fill, stroke) => ({ tag: 'path', attrs: { d: 'M 0 10 L 8 5.5 L 16 10 L 8 14.5 Z', fill, stroke, 'stroke-width': 1 } }),
  },
  'default-start': {
    ref: { x: -2, y: 10 },
    shape: (_fill, stroke) => ({ tag: 'path', attrs: { d: 'M 6 4 L 11 16', fill: 'none', stroke, 'stroke-width': 1.5 } }),
  },
}

function colorKey(color: string): string {
  return color.replace(/[^a-zA-Z0-9]/g, '')
}

let markerFactoryCounter = 0

export class MarkerFactory {
  private readonly created = new Set<string>()
  private readonly prefix: string

  constructor(private readonly getSvg: () => SVGSVGElement) {
    this.prefix = `fa-bpmn-${++markerFactoryCounter}`
  }

  /** Liefert `url(#…)` für den Marker und legt ihn bei Bedarf an. */
  url(type: MarkerType, fill: string, stroke: string): string {
    const id = `${this.prefix}-${type}-${colorKey(fill)}-${colorKey(stroke)}`
    if (!this.created.has(id)) {
      this.create(id, MARKERS[type], fill, stroke)
      this.created.add(id)
    }
    return `url(#${id})`
  }

  private create(id: string, spec: MarkerSpec, fill: string, stroke: string): void {
    const svg = this.getSvg()
    let defs = (Array.from(svg.children).find((child) => child.localName === 'defs') as SVGElement | undefined) || null
    if (!defs) defs = svgElement(svg, 'defs', {})
    const marker = svgElement(defs, 'marker', {
      id,
      viewBox: '0 0 20 20',
      refX: spec.ref.x,
      refY: spec.ref.y,
      markerWidth: 20,
      markerHeight: 20,
      markerUnits: 'userSpaceOnUse',
      orient: 'auto',
    })
    const shape = spec.shape(fill, stroke)
    svgElement(marker, shape.tag, shape.attrs)
  }
}
