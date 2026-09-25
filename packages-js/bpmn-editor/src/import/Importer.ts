/**
 * Import: Aus `bpmn:Definitions` samt DI werden Diagrammelemente erzeugt.
 *
 * Ablauf (eigene Umsetzung):
 * 1. Hauptebene (`bpmndi:BPMNPlane`) rendern: Pools → Bahnen → Knoten →
 *    Randereignisse → Kanten (Sequenz-, Nachrichtenflüsse, Assoziationen).
 * 2. Weitere Ebenen (zugeklappte Teilprozesse) als zusätzliche Wurzeln.
 *
 * Elemente ohne DI bleiben im semantischen Modell unverändert erhalten; sie
 * werden nur nicht angezeigt (Warnung).
 */

import { getExternalLabelBounds, getLabel, isLabelExternal } from '../util/LabelUtil'
import { is, isExpanded } from '../util/ModelUtil'
import type { BpmnElement, Canvas, ElementRegistry, EventBus, ModdleElement, Point, Translate } from '../types'
import type ElementFactory from '../modeling/ElementFactory'
import PlaneWalker from './PlaneWalker'

export interface ImportResult {
  warnings: string[]
}

export class BpmnImporter {
  static $inject = ['eventBus', 'canvas', 'elementFactory', 'elementRegistry', 'translate']

  constructor(
    private readonly eventBus: EventBus,
    private readonly canvas: Canvas,
    private readonly elementFactory: ElementFactory,
    private readonly elementRegistry: ElementRegistry,
    readonly translate: Translate,
  ) {}

  /** Importiert die Definitionen; `diagram` wählt die Hauptebene. */
  importDefinitions(definitions: ModdleElement, diagram?: ModdleElement): ImportResult {
    const warnings: string[] = []
    const diagrams = definitions.get<ModdleElement[]>('diagrams') || []
    const main = diagram || diagrams[0]
    if (!main || !main.plane) {
      warnings.push(this.translate('No diagram interchange (DI) found; elements without position are not displayed'))
      return { warnings }
    }
    new PlaneWalker(this, warnings).walk(main.plane, true)
    for (const other of diagrams) {
      if (other === main || !other.plane) continue
      if (other.plane.bpmnElement && is(other.plane.bpmnElement, 'bpmn:SubProcess')) new PlaneWalker(this, warnings).walk(other.plane, false)
      else warnings.push(this.translate('Additional diagram {id} is kept but not displayed', { id: other.id || '?' }))
    }
    return { warnings }
  }

  createRoot(bo: ModdleElement, plane: ModdleElement, isMain: boolean): BpmnElement {
    const id = isMain ? bo.id : `${bo.id}_plane`
    const root = this.elementFactory.createRoot({ id, businessObject: bo, di: plane }) as unknown as BpmnElement
    if (isMain) this.canvas.setRootElement(root as never)
    else this.canvas.addRootElement(root as never)
    return root
  }

  addShape(bo: ModdleElement, di: ModdleElement, parent: BpmnElement, extra: Record<string, unknown> = {}): BpmnElement {
    const bounds = di.bounds
    const attrs: Record<string, unknown> = {
      id: bo.id,
      businessObject: bo,
      di,
      x: Math.round(bounds?.x ?? 0),
      y: Math.round(bounds?.y ?? 0),
      width: Math.round(bounds?.width ?? 0),
      height: Math.round(bounds?.height ?? 0),
      ...extra,
    }
    if (is(bo, 'bpmn:SubProcess')) attrs.collapsed = !isExpanded(bo, di)
    const shape = this.elementFactory.createShape(attrs) as unknown as BpmnElement
    if (this.elementRegistry.get(shape.id)) throw new Error(this.translate('Element {id} exists more than once', { id: shape.id }))
    this.canvas.addShape(shape as never, parent as never)
    this.addLabel(shape)
    this.eventBus.fire('bpmnElement.added', { element: shape })
    return shape
  }

  addConnection(bo: ModdleElement, di: ModdleElement, parent: BpmnElement, source: BpmnElement, target: BpmnElement): BpmnElement {
    const waypoints: Point[] = (di.waypoint || []).map((point) => ({ x: point.x ?? 0, y: point.y ?? 0 }))
    const connection = this.elementFactory.createConnection({ id: bo.id, businessObject: bo, di, source, target, waypoints }) as unknown as BpmnElement
    this.canvas.addConnection(connection as never, parent as never)
    this.addLabel(connection)
    this.eventBus.fire('bpmnElement.added', { element: connection })
    return connection
  }

  private addLabel(element: BpmnElement): void {
    if (!isLabelExternal(element) || !getLabel(element)) return
    const bounds = getExternalLabelBounds(element.di, element)
    const label = this.elementFactory.createLabel({
      id: `${element.id}_label`,
      labelTarget: element,
      type: 'label',
      businessObject: element.businessObject,
      di: element.di,
      x: Math.round(bounds.x),
      y: Math.round(bounds.y),
      width: Math.round(bounds.width),
      height: Math.round(bounds.height),
    })
    this.canvas.addShape(label as never, element.parent as never)
  }
}

export default BpmnImporter
