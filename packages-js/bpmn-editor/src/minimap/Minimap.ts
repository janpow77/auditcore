/**
 * Übersichtskarte (Minimap): verkleinerte Darstellung der aktiven Ebene mit
 * dem sichtbaren Ausschnitt; Klicken oder Ziehen verschiebt den Ausschnitt.
 */

import { computeContentBounds } from '../export/SvgExport'
import { toolIcons } from '../icons/Icons'
import type { Bounds, Canvas, ElementRegistry, EventBus, Translate } from '../types'

const SVG_NS = 'http://www.w3.org/2000/svg'
const WIDTH = 220
const HEIGHT = 150
const PADDING = 40

let minimapCounter = 0

export default class Minimap {
  static $inject = ['eventBus', 'canvas', 'elementRegistry', 'translate', 'config.minimap']

  private readonly container: HTMLDivElement
  private readonly svg: SVGSVGElement
  private readonly use: SVGUseElement
  private readonly viewportRect: SVGRectElement
  private readonly toggleButton: HTMLButtonElement
  private open_ = false
  private scheduled = false
  private dragging = false
  private diagramBounds: Bounds = { x: 0, y: 0, width: WIDTH, height: HEIGHT }
  private readonly layerId: string

  constructor(
    private readonly eventBus: EventBus,
    private readonly canvas: Canvas,
    private readonly elementRegistry: ElementRegistry,
    private readonly translate: Translate,
    config?: { open?: boolean },
  ) {
    this.layerId = `fa-minimap-layer-${++minimapCounter}`
    this.container = document.createElement('div')
    this.container.className = 'fa-minimap'
    this.toggleButton = document.createElement('button')
    this.toggleButton.type = 'button'
    this.toggleButton.className = 'fa-minimap-toggle'
    this.toggleButton.innerHTML = toolIcons.minimap
    this.toggleButton.addEventListener('click', () => this.toggle())
    this.svg = document.createElementNS(SVG_NS, 'svg') as SVGSVGElement
    this.svg.setAttribute('class', 'fa-minimap-map')
    this.svg.setAttribute('width', String(WIDTH))
    this.svg.setAttribute('height', String(HEIGHT))
    this.svg.setAttribute('role', 'img')
    this.use = document.createElementNS(SVG_NS, 'use') as SVGUseElement
    this.viewportRect = document.createElementNS(SVG_NS, 'rect') as SVGRectElement
    this.viewportRect.setAttribute('class', 'fa-minimap-viewport')
    this.svg.appendChild(this.use)
    this.svg.appendChild(this.viewportRect)
    this.container.appendChild(this.toggleButton)
    this.container.appendChild(this.svg)
    canvas.getContainer().appendChild(this.container)
    this.updateTexts()

    this.svg.addEventListener('mousedown', (event) => this.onPointerDown(event))
    window.addEventListener('mousemove', this.onPointerMove)
    window.addEventListener('mouseup', this.onPointerUp)

    eventBus.on(['canvas.viewbox.changed', 'elements.changed', 'root.set', 'import.done', 'canvas.resized'], () => this.schedule())
    eventBus.on('diagram.destroy', () => this.destroy())
    if (config?.open) this.open()
    else this.close()
  }

  isOpen(): boolean {
    return this.open_
  }

  open(): void {
    this.open_ = true
    this.container.classList.add('open')
    this.updateTexts()
    this.update()
    this.eventBus.fire('minimap.toggle', { open: true })
  }

  close(): void {
    this.open_ = false
    this.container.classList.remove('open')
    this.updateTexts()
    this.eventBus.fire('minimap.toggle', { open: false })
  }

  toggle(open?: boolean): void {
    const next = open === undefined ? !this.open_ : open
    if (next) this.open()
    else this.close()
  }

  /** Aktualisiert Karte und Ausschnitt sofort. */
  update(): void {
    this.scheduled = false
    if (!this.open_) return
    const layer = this.canvas.getActiveLayer() as SVGGElement | null
    if (!layer) return
    layer.setAttribute('id', this.layerId)
    this.use.setAttribute('href', `#${this.layerId}`)
    const root = this.canvas.getRootElement()
    const elements = this.elementRegistry.filter((element) => element !== root && this.canvas.findRoot(element) === root)
    const content = computeContentBounds(elements)
    const viewbox = this.canvas.viewbox()
    this.diagramBounds = union(pad(content, PADDING), { x: viewbox.x, y: viewbox.y, width: viewbox.width, height: viewbox.height })
    const b = this.diagramBounds
    this.svg.setAttribute('viewBox', `${b.x} ${b.y} ${Math.max(b.width, 1)} ${Math.max(b.height, 1)}`)
    this.viewportRect.setAttribute('x', String(viewbox.x))
    this.viewportRect.setAttribute('y', String(viewbox.y))
    this.viewportRect.setAttribute('width', String(Math.max(viewbox.width, 0)))
    this.viewportRect.setAttribute('height', String(Math.max(viewbox.height, 0)))
  }

  private schedule(): void {
    if (this.scheduled || !this.open_) return
    this.scheduled = true
    const run = () => this.update()
    if (typeof requestAnimationFrame === 'function') requestAnimationFrame(run)
    else setTimeout(run, 0)
  }

  /** Zentriert den Ausschnitt auf einen Punkt der Karte (Client-Koordinaten). */
  centerOnClientPoint(clientX: number, clientY: number): void {
    const rect = this.svg.getBoundingClientRect()
    const b = this.diagramBounds
    const scale = Math.min(WIDTH / b.width, HEIGHT / b.height) || 1
    const offsetX = (WIDTH - b.width * scale) / 2
    const offsetY = (HEIGHT - b.height * scale) / 2
    const x = b.x + (clientX - rect.left - offsetX) / scale
    const y = b.y + (clientY - rect.top - offsetY) / scale
    this.centerOn({ x, y })
  }

  centerOn(point: { x: number; y: number }): void {
    const viewbox = this.canvas.viewbox()
    this.canvas.viewbox({
      x: point.x - viewbox.width / 2,
      y: point.y - viewbox.height / 2,
      width: viewbox.width,
      height: viewbox.height,
    })
  }

  private onPointerDown(event: MouseEvent): void {
    event.preventDefault()
    this.dragging = true
    this.centerOnClientPoint(event.clientX, event.clientY)
  }

  private onPointerMove = (event: MouseEvent): void => {
    if (this.dragging) this.centerOnClientPoint(event.clientX, event.clientY)
  }

  private onPointerUp = (): void => {
    this.dragging = false
  }

  private updateTexts(): void {
    const label = this.translate(this.open_ ? 'Close minimap' : 'Open minimap')
    this.toggleButton.title = label
    this.toggleButton.setAttribute('aria-label', label)
    this.toggleButton.setAttribute('aria-pressed', String(this.open_))
    this.svg.setAttribute('aria-label', this.translate('Minimap'))
  }

  private destroy(): void {
    window.removeEventListener('mousemove', this.onPointerMove)
    window.removeEventListener('mouseup', this.onPointerUp)
    this.container.parentNode?.removeChild(this.container)
  }
}

function pad(bounds: Bounds, padding: number): Bounds {
  return { x: bounds.x - padding, y: bounds.y - padding, width: bounds.width + padding * 2, height: bounds.height + padding * 2 }
}

function union(a: Bounds, b: Bounds): Bounds {
  const x = Math.min(a.x, b.x)
  const y = Math.min(a.y, b.y)
  return {
    x,
    y,
    width: Math.max(a.x + a.width, b.x + b.width) - x,
    height: Math.max(a.y + a.height, b.y + b.height) - y,
  }
}
