/**
 * Ebenen für zugeklappte Teilprozesse (BPMN-DI: eigenes `BPMNDiagram`,
 * dessen Ebene auf den Teilprozess verweist).
 *
 * - Hineinzoomen (Drill-down) über eine Schaltfläche am Teilprozess,
 *   Brotkrumen-Navigation zurück.
 * - Auf-/Zuklappen verschiebt den Inhalt zwischen Teilprozess und Ebene.
 */

import type { Element } from 'diagram-js/lib/model/Types'

import { toolIcons } from '../icons/Icons'
import { getLabel } from '../util/LabelUtil'
import { getBusinessObject, getDefinitions, is, isExpanded, removeFromList, addToList } from '../util/ModelUtil'
import type BpmnFactory from '../modeling/BpmnFactory'
import type ElementFactory from '../modeling/ElementFactory'
import type Modeling from '../modeling/Modeling'
import type { BpmnElement, Canvas, CommandStack, ElementRegistry, EventBus, ModdleElement, Overlays, Translate } from '../types'

const PADDING = 40

interface PlaneContext {
  businessObject: ModdleElement
  root?: BpmnElement
  diagram?: ModdleElement
  index?: number
}

/** Befehl: Ebene für einen Teilprozess anlegen. */
export class AddPlaneHandler {
  static $inject = ['canvas', 'bpmnFactory', 'elementFactory']

  constructor(
    private readonly canvas: Canvas,
    private readonly bpmnFactory: BpmnFactory,
    private readonly elementFactory: ElementFactory,
  ) {}

  execute(context: PlaneContext): BpmnElement[] {
    const bo = context.businessObject
    const definitions = getDefinitions(bo)
    if (!context.diagram) {
      const plane = this.bpmnFactory.createDiPlane(bo)
      const diagram = this.bpmnFactory.createDiDiagram(plane)
      plane.$parent = diagram
      context.diagram = diagram
      context.root = this.elementFactory.createRoot({ id: `${bo.id}_plane`, businessObject: bo, di: plane }) as BpmnElement
    }
    const diagram = context.diagram as ModdleElement
    diagram.$parent = definitions
    addToList(definitions.get('diagrams'), diagram)
    this.canvas.addRootElement(context.root as never)
    return []
  }

  revert(context: PlaneContext): BpmnElement[] {
    const definitions = getDefinitions(context.businessObject)
    removeFromList(definitions.get('diagrams'), context.diagram)
    this.canvas.removeRootElement(context.root as never)
    return []
  }
}

/** Befehl: Ebene eines Teilprozesses entfernen. */
export class RemovePlaneHandler {
  static $inject = ['canvas']

  constructor(private readonly canvas: Canvas) {}

  execute(context: PlaneContext): BpmnElement[] {
    const root = context.root as BpmnElement
    const diagram = (root.di as ModdleElement).$parent as ModdleElement
    const definitions = getDefinitions(context.businessObject)
    context.diagram = diagram
    context.index = removeFromList(definitions.get('diagrams'), diagram)
    this.canvas.removeRootElement(root as never)
    return []
  }

  revert(context: PlaneContext): BpmnElement[] {
    const definitions = getDefinitions(context.businessObject)
    addToList(definitions.get('diagrams'), context.diagram, context.index)
    this.canvas.addRootElement(context.root as never)
    return []
  }
}

export default class SubProcessPlanes {
  static $inject = ['eventBus', 'canvas', 'modeling', 'commandStack', 'overlays', 'translate', 'elementRegistry']

  private readonly breadcrumbs: HTMLElement

  constructor(
    private readonly eventBus: EventBus,
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
    eventBus.on('root.set', () => this.renderBreadcrumbs())
    eventBus.on('import.done', () => this.renderBreadcrumbs())
    eventBus.on('shape.remove', (event: { element: BpmnElement }) => this.overlays.remove({ element: event.element, type: 'fa-drilldown' } as never))
    eventBus.on('diagram.destroy', () => this.breadcrumbs.parentNode?.removeChild(this.breadcrumbs))
  }

  /** Wurzel (Ebene) eines Teilprozesses, falls vorhanden. */
  getPlaneRoot(bo: ModdleElement): BpmnElement | undefined {
    return (this.canvas.getRootElements() as BpmnElement[]).find((root) => root.businessObject === bo && is(root, 'bpmn:SubProcess'))
  }

  /** Legt bei Bedarf die Ebene an und liefert deren Wurzel. */
  ensurePlane(bo: ModdleElement): BpmnElement {
    const existing = this.getPlaneRoot(bo)
    if (existing) return existing
    const context: PlaneContext = { businessObject: bo }
    this.eventBus.fire('subprocess.plane.create', context)
    this.commandStack.execute('subprocess.addPlane', context as never)
    return context.root as BpmnElement
  }

  /** Wechselt in die Ebene des zugeklappten Teilprozesses. */
  drillDown(element: BpmnElement): void {
    const root = this.ensurePlane(getBusinessObject(element))
    this.canvas.setRootElement(root as never)
    this.canvas.zoom('fit-viewport')
  }

  /** Zurück zur übergeordneten Ebene. */
  drillUp(): void {
    const current = this.canvas.getRootElement() as BpmnElement
    if (!is(current, 'bpmn:SubProcess')) return
    const parentRoot = this.findRootContaining(getBusinessObject(current))
    if (parentRoot) this.canvas.setRootElement(parentRoot as never)
  }

  /** Klappt einen Teilprozess auf bzw. zu (ein Rückgängig-Schritt). */
  toggleExpanded(shape: BpmnElement, expand?: boolean): void {
    const target = expand === undefined ? !isExpanded(shape) : expand
    if (target === isExpanded(shape)) return
    this.modeling.compound(() => (target ? this.expand(shape) : this.collapse(shape)))
  }

  private collapse(shape: BpmnElement): void {
    const bo = getBusinessObject(shape)
    const children = ((shape.children || []) as BpmnElement[]).filter((child) => !child.labelTarget)
    const root = this.ensurePlane(bo)
    if (children.length) {
      const box = bbox(children)
      this.modeling.moveElements(children as never, { x: PADDING * 3 - box.x, y: PADDING * 3 - box.y }, root as never, { autoResize: false } as never)
    }
    this.modeling.updateModdleProperties(shape, shape.di as ModdleElement, { isExpanded: false })
    const center = { x: shape.x + shape.width / 2, y: shape.y + shape.height / 2 }
    this.modeling.resizeShape(shape as never, { x: Math.round(center.x - 50), y: Math.round(center.y - 40), width: 100, height: 80 })
  }

  private expand(shape: BpmnElement): void {
    const bo = getBusinessObject(shape)
    const root = this.getPlaneRoot(bo)
    const children = root ? ((root.children || []) as BpmnElement[]).filter((child) => !child.labelTarget) : []
    this.modeling.updateModdleProperties(shape, shape.di as ModdleElement, { isExpanded: true })
    const box = children.length ? bbox(children) : { x: 0, y: 0, width: 250, height: 120 }
    const width = Math.max(350, box.width + PADDING * 2)
    const height = Math.max(200, box.height + PADDING * 2)
    this.modeling.resizeShape(shape as never, { x: shape.x, y: shape.y, width, height }, null as never, { autoResize: false } as never)
    if (children.length) {
      const delta = { x: shape.x + PADDING - box.x, y: shape.y + PADDING - box.y }
      this.modeling.moveElements(children as never, delta, shape as never, { autoResize: false } as never)
    }
    if (root) {
      this.commandStack.execute('subprocess.removePlane', { businessObject: bo, root } as never)
    }
  }

  private findRootContaining(bo: ModdleElement): BpmnElement | undefined {
    const parentBo = bo.$parent
    const roots = this.canvas.getRootElements() as BpmnElement[]
    if (parentBo && is(parentBo, 'bpmn:SubProcess')) {
      const plane = roots.find((root) => root.businessObject === parentBo)
      if (plane) return plane
    }
    return roots.find((root) => !is(root, 'bpmn:SubProcess')) || roots[0]
  }

  private refreshOverlays(): void {
    const root = this.canvas.getRootElement() as BpmnElement
    const elements = this.elementRegistry.filter((element) => is(element, 'bpmn:SubProcess') && !!element.parent && !element.labelTarget)
    for (const element of elements) {
      this.overlays.remove({ element, type: 'fa-drilldown' } as never)
      if (isExpanded(element) || this.canvas.findRoot(element as never) !== root) continue
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
      this.overlays.add(element as never, 'fa-drilldown', { position: { bottom: -7, right: -8 }, html: button })
    }
  }

  private renderBreadcrumbs(): void {
    const chain: BpmnElement[] = []
    let current: BpmnElement | undefined = this.canvas.getRootElement() as BpmnElement
    while (current) {
      chain.unshift(current)
      current = is(current, 'bpmn:SubProcess') ? this.findRootContaining(getBusinessObject(current)) : undefined
    }
    this.breadcrumbs.innerHTML = ''
    this.breadcrumbs.style.display = chain.length > 1 ? '' : 'none'
    chain.forEach((root, index) => {
      const item = document.createElement(index === chain.length - 1 ? 'span' : 'button')
      item.className = 'fa-breadcrumb'
      item.textContent = getLabel(root) || this.translate(is(root, 'bpmn:SubProcess') ? 'Sub-process' : 'Process')
      if (item instanceof HTMLButtonElement) {
        item.type = 'button'
        item.addEventListener('click', () => this.canvas.setRootElement(root as never))
      } else {
        item.setAttribute('aria-current', 'page')
      }
      this.breadcrumbs.appendChild(item)
    })
  }
}

function bbox(elements: Element[]): { x: number; y: number; width: number; height: number } {
  let minX = Infinity
  let minY = Infinity
  let maxX = -Infinity
  let maxY = -Infinity
  for (const element of elements) {
    const points = (element as { waypoints?: { x: number; y: number }[] }).waypoints
    if (points) {
      for (const point of points) {
        minX = Math.min(minX, point.x)
        minY = Math.min(minY, point.y)
        maxX = Math.max(maxX, point.x)
        maxY = Math.max(maxY, point.y)
      }
      continue
    }
    const shape = element as unknown as { x: number; y: number; width: number; height: number }
    minX = Math.min(minX, shape.x)
    minY = Math.min(minY, shape.y)
    maxX = Math.max(maxX, shape.x + shape.width)
    maxY = Math.max(maxY, shape.y + shape.height)
  }
  return { x: minX, y: minY, width: maxX - minX, height: maxY - minY }
}
