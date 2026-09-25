/**
 * Punktraster im Hintergrund (nur Anzeige, nicht im Export).
 */

import type { Canvas, EventBus } from '../types'

const SVG_NS = 'http://www.w3.org/2000/svg'
let gridCounter = 0

export default class GridDisplay {
  static $inject = ['eventBus', 'canvas', 'config.gridSize', 'config.grid']

  private readonly rect: SVGRectElement
  private visible: boolean

  constructor(
    eventBus: EventBus,
    private readonly canvas: Canvas,
    gridSize: number | undefined,
    config?: { visible?: boolean },
  ) {
    const spacing = gridSize && gridSize > 0 ? gridSize : 10
    const id = `fa-grid-pattern-${++gridCounter}`
    const layer = canvas.getLayer('fa-grid', -2) as unknown as SVGGElement
    const pattern = document.createElementNS(SVG_NS, 'pattern')
    pattern.setAttribute('id', id)
    pattern.setAttribute('width', String(spacing))
    pattern.setAttribute('height', String(spacing))
    pattern.setAttribute('patternUnits', 'userSpaceOnUse')
    const dot = document.createElementNS(SVG_NS, 'circle')
    dot.setAttribute('cx', '0.5')
    dot.setAttribute('cy', '0.5')
    dot.setAttribute('r', '0.6')
    dot.setAttribute('class', 'fa-grid-dot')
    pattern.appendChild(dot)
    const defs = document.createElementNS(SVG_NS, 'defs')
    defs.appendChild(pattern)
    layer.appendChild(defs)
    this.rect = document.createElementNS(SVG_NS, 'rect') as SVGRectElement
    this.rect.setAttribute('fill', `url(#${id})`)
    this.rect.setAttribute('class', 'fa-grid')
    layer.appendChild(this.rect)
    this.visible = config?.visible !== false
    eventBus.on(['canvas.viewbox.changed', 'canvas.resized', 'import.done'], () => this.update())
    this.update()
  }

  isVisible(): boolean {
    return this.visible
  }

  toggle(visible?: boolean): void {
    this.visible = visible === undefined ? !this.visible : visible
    this.update()
  }

  private update(): void {
    this.rect.style.display = this.visible ? '' : 'none'
    if (!this.visible) return
    let viewbox
    try {
      viewbox = this.canvas.viewbox()
    } catch {
      return
    }
    const margin = 100
    this.rect.setAttribute('x', String(Math.floor(viewbox.x - margin)))
    this.rect.setAttribute('y', String(Math.floor(viewbox.y - margin)))
    this.rect.setAttribute('width', String(Math.ceil(Math.max(viewbox.width, 0) + margin * 2)))
    this.rect.setAttribute('height', String(Math.ceil(Math.max(viewbox.height, 0) + margin * 2)))
  }
}
