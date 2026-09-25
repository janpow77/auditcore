/**
 * Ebenen für zugeklappte Teilprozesse (BPMN-DI: eigenes `BPMNDiagram`,
 * dessen Ebene auf den Teilprozess verweist).
 *
 * - Hineinzoomen (Drill-down) über eine Schaltfläche am Teilprozess,
 *   Brotkrumen-Navigation zurück.
 * - Auf-/Zuklappen verschiebt den Inhalt zwischen Teilprozess und Ebene.
 */

import { toolIcons } from '../icons/Icons'
import { getBusinessObject, is, isExpanded } from '../util/ModelUtil'
import { toBounds } from '../modeling/LaneUtil'
import type { BpmnElement, Bounds, Canvas, CommandStack, ElementRegistry, EventBus, ModdleElement, Overlays, Point, Translate } from '../types'
import type Modeling from '../modeling/Modeling'
import { renderBreadcrumbs } from './Breadcrumbs'
import { AddPlaneHandler, RemovePlaneHandler, type PlaneContext } from './PlaneHandlers'

const PADDING = 40
const OVERLAY_TYPE = 'fa-drilldown'

function contentOf(element: BpmnElement | undefined): BpmnElement[] {
  return ((element?.children || []) as BpmnElement[]).filter((child) => !child.labelTarget)
}

function boundingBox(elements: BpmnElement[]): Bounds {
  const points: Point[] = elements.flatMap((element) => {
    if (element.waypoints) return element.waypoints as Point[]
    const box = toBounds(element)
    return [
      { x: box.x, y: box.y },
      { x: box.x + box.width, y: box.y + box.height },
    ]
  })
  const xs = points.map((point) => point.x)
  const ys = points.map((point) => point.y)
  const x = Math.min(...xs)
  const y = Math.min(...ys)
  return { x, y, width: Math.max(...xs) - x, height: Math.max(...ys) - y }
}

export default class SubProcessPlanes {
  static $inject = ['eventBus', 'canvas', 'modeling', 'commandStack', 'overlays', 'translate', 'elementRegistry']

  private readonly breadcrumbs: HTMLElement

  constructor(
    eventBus: EventBus,
    private readonly canvas: Canvas,
    private readonly modeling: Modeling,
    private readonly commandStack: CommandStack,
    private readonly overlays: Overlays,
    private readonly translate: Translate,
    private readonly elementRegistry: ElementRegistry,
  ) {
    commandStack.registerHandler('subprocess.addPlane', AddPlaneHandler as never)
    commandStack.registerHandler('subprocess.removePlane', RemovePlaneHandler as never)
    this.breadcrumbs = document.createElement('nav')
    this.breadcrumbs.className = 'fa-breadcrumbs'
    this.breadcrumbs.setAttribute('aria-label', translate('Diagram levels'))
    canvas.getContainer().appendChild(this.breadcrumbs)
    eventBus.on(['import.done', 'elements.changed', 'root.set'], () => this.refreshOverlays())
    eventBus.on(['import.done', 'root.set'], () => this.updateBreadcrumbs())
    eventBus.on('diagram.destroy', () => this.breadcrumbs.remove())
  }

  /** Wurzel (Ebene) eines Teilprozesses, falls vorhanden. */
  getPlaneRoot(bo: ModdleElement): BpmnElement | undefined {
    return (this.canvas.getRootElements() as unknown as BpmnElement[]).find((root) => root.businessObject === bo && is(root, 'bpmn:SubProcess'))
  }

  /** Legt bei Bedarf die Ebene an und liefert deren Wurzel. */
  ensurePlane(bo: ModdleElement): BpmnElement {
    const existing = this.getPlaneRoot(bo)
    if (existing) return existing
    const context: PlaneContext = { businessObject: bo }
    this.commandStack.execute('subprocess.addPlane', context as never)
    return context.root as BpmnElement
  }

  /** Wechselt in die Ebene des zugeklappten Teilprozesses. */
  drillDown(element: BpmnElement): void {
    this.canvas.setRootElement(this.ensurePlane(getBusinessObject(element)) as never)
    this.canvas.zoom('fit-viewport')
  }

  /** Zurück zur übergeordneten Ebene. */
  drillUp(): void {
    const current = this.canvas.getRootElement() as unknown as BpmnElement
    if (!is(current, 'bpmn:SubProcess')) return
    const parent = this.parentRoot(getBusinessObject(current))
    if (parent) this.canvas.setRootElement(parent as never)
  }

  /** Klappt einen Teilprozess auf bzw. zu (ein Rückgängig-Schritt). */
  toggleExpanded(shape: BpmnElement, expand?: boolean): void {
    const target = expand === undefined ? !isExpanded(shape) : expand
    if (target === isExpanded(shape)) return
    this.modeling.compound(() => (target ? this.expand(shape) : this.collapse(shape)))
  }

  private collapse(shape: BpmnElement): void {
    const children = contentOf(shape)
    const root = this.ensurePlane(getBusinessObject(shape))
    if (children.length) {
      const box = boundingBox(children)
      this.modeling.moveElements(children as never, { x: PADDING * 3 - box.x, y: PADDING * 3 - box.y }, root as never, { autoResize: false } as never)
    }
    this.modeling.updateModdleProperties(shape, shape.di as ModdleElement, { isExpanded: false })
    const bounds = toBounds(shape)
    const center = { x: bounds.x + bounds.width / 2, y: bounds.y + bounds.height / 2 }
    this.modeling.resizeShape(shape as never, { x: Math.round(center.x - 50), y: Math.round(center.y - 40), width: 100, height: 80 })
  }

  private expand(shape: BpmnElement): void {
    const bo = getBusinessObject(shape)
    const root = this.getPlaneRoot(bo)
    const children = contentOf(root)
    this.modeling.updateModdleProperties(shape, shape.di as ModdleElement, { isExpanded: true })
    const box = children.length ? boundingBox(children) : { x: 0, y: 0, width: 250, height: 120 }
    const bounds = toBounds(shape)
    const next = { x: bounds.x, y: bounds.y, width: Math.max(350, box.width + PADDING * 2), height: Math.max(200, box.height + PADDING * 2) }
    this.modeling.resizeShape(shape as never, next, undefined, { autoResize: false } as never)
    if (children.length) {
      const delta = { x: bounds.x + PADDING - box.x, y: bounds.y + PADDING - box.y }
      this.modeling.moveElements(children as never, delta, shape as never, { autoResize: false } as never)
    }
    if (root) this.commandStack.execute('subprocess.removePlane', { businessObject: bo, root } as never)
  }

  private parentRoot(bo: ModdleElement): BpmnElement | undefined {
    const roots = this.canvas.getRootElements() as unknown as BpmnElement[]
    const parentBo = bo.$parent
    const plane = parentBo && is(parentBo, 'bpmn:SubProcess') ? roots.find((root) => root.businessObject === parentBo) : undefined
    return plane || roots.find((root) => !is(root, 'bpmn:SubProcess')) || roots[0]
  }

  private refreshOverlays(): void {
    const root = this.canvas.getRootElement()
    const subProcesses = this.elementRegistry.filter((element) => is(element, 'bpmn:SubProcess') && !!element.parent && !element.labelTarget)
    for (const element of subProcesses) {
      this.overlays.remove({ element, type: OVERLAY_TYPE } as never)
      if (!isExpanded(element) && this.canvas.findRoot(element as never) === root) this.addOverlay(element)
    }
  }

  private addOverlay(element: BpmnElement): void {
    const button = document.createElement('button')
    button.type = 'button'
    button.className = 'fa-drilldown-button'
    button.title = this.translate('Open sub-process')
    button.setAttribute('aria-label', button.title)
    button.innerHTML = toolIcons.drilldown
    button.addEventListener('click', (event) => {
      event.stopPropagation()
      this.drillDown(element)
    })
    this.overlays.add(element as never, OVERLAY_TYPE, { position: { bottom: -7, right: -8 }, html: button })
  }

  private updateBreadcrumbs(): void {
    const chain: BpmnElement[] = []
    let current: BpmnElement | undefined = this.canvas.getRootElement() as unknown as BpmnElement
    while (current) {
      chain.unshift(current)
      current = is(current, 'bpmn:SubProcess') ? this.parentRoot(getBusinessObject(current)) : undefined
      if (current && chain.includes(current)) break
    }
    renderBreadcrumbs(this.breadcrumbs, chain, this.translate, (root) => this.canvas.setRootElement(root as never))
  }
}
