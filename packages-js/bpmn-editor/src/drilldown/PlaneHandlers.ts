/**
 * Befehle zum Anlegen und Entfernen der Ebene eines zugeklappten
 * Teilprozesses (eigenes `bpmndi:BPMNDiagram` mit Ebene).
 */

import { addToList, getDefinitions, removeFromList } from '../util/ModelUtil'
import type { BpmnElement, Canvas, ModdleElement } from '../types'
import type BpmnFactory from '../modeling/BpmnFactory'
import type ElementFactory from '../modeling/ElementFactory'

export interface PlaneContext {
  businessObject: ModdleElement
  root?: BpmnElement
  diagram?: ModdleElement
  index?: number
}

function diagramsOf(bo: ModdleElement): ModdleElement[] {
  const definitions = getDefinitions(bo)
  if (!definitions) throw new Error('Teilprozess gehört zu keinen Definitionen')
  return definitions.get<ModdleElement[]>('diagrams')
}

export class AddPlaneHandler {
  static $inject = ['canvas', 'bpmnFactory', 'elementFactory']

  constructor(
    private readonly canvas: Canvas,
    private readonly bpmnFactory: BpmnFactory,
    private readonly elementFactory: ElementFactory,
  ) {}

  execute(context: PlaneContext): BpmnElement[] {
    const bo = context.businessObject
    if (!context.diagram || !context.root) {
      const plane = this.bpmnFactory.createDiPlane(bo)
      const diagram = this.bpmnFactory.createDiDiagram(plane)
      plane.$parent = diagram
      context.diagram = diagram
      context.root = this.elementFactory.createRoot({ id: `${bo.id}_plane`, businessObject: bo, di: plane }) as unknown as BpmnElement
    }
    context.diagram.$parent = getDefinitions(bo)
    addToList(diagramsOf(bo), context.diagram)
    this.canvas.addRootElement(context.root as never)
    return []
  }

  revert(context: PlaneContext): BpmnElement[] {
    if (context.diagram) removeFromList(diagramsOf(context.businessObject), context.diagram)
    if (context.root) this.canvas.removeRootElement(context.root as never)
    return []
  }
}

export class RemovePlaneHandler {
  static $inject = ['canvas']

  constructor(private readonly canvas: Canvas) {}

  execute(context: PlaneContext): BpmnElement[] {
    const root = context.root
    const diagram = root?.di?.$parent || undefined
    if (!root || !diagram) return []
    context.diagram = diagram
    context.index = removeFromList(diagramsOf(context.businessObject), diagram)
    this.canvas.removeRootElement(root as never)
    return []
  }

  revert(context: PlaneContext): BpmnElement[] {
    if (!context.root || !context.diagram) return []
    addToList(diagramsOf(context.businessObject), context.diagram, context.index)
    this.canvas.addRootElement(context.root as never)
    return []
  }
}
