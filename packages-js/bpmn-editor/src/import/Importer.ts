/**
 * Import: Aus `bpmn:Definitions` samt DI werden Diagrammelemente erzeugt.
 *
 * Ablauf (eigene Umsetzung):
 * 1. Alle Ebenen (`bpmndi:BPMNPlane`) einsammeln und DI je semantischem
 *    Objekt zuordnen.
 * 2. Hauptebene rendern: Pools → Bahnen → Knoten → Randereignisse →
 *    Kanten (Sequenz-, Nachrichtenflüsse, Assoziationen).
 * 3. Weitere Ebenen (zugeklappte Teilprozesse) als zusätzliche Wurzeln.
 *
 * Elemente ohne DI bleiben im semantischen Modell unverändert erhalten; sie
 * werden nur nicht angezeigt (Warnung).
 */

import { getExternalLabelBounds, getLabel, isLabelExternal } from '../util/LabelUtil'
import { is, isExpanded, type ModdleElement } from '../util/ModelUtil'

/* eslint-disable @typescript-eslint/no-explicit-any */

export interface ImportResult {
  warnings: string[]
}

type Deferred = () => void

export class BpmnImporter {
  static $inject = ['eventBus', 'canvas', 'elementFactory', 'elementRegistry', 'translate']

  constructor(
    private _eventBus: any,
    private _canvas: any,
    private _elementFactory: any,
    private _elementRegistry: any,
    private _translate: (text: string, replacements?: Record<string, string>) => string,
  ) {}

  /** Importiert die Definitionen; `diagram` wählt die Hauptebene. */
  importDefinitions(definitions: ModdleElement, diagram?: ModdleElement): ImportResult {
    const warnings: string[] = []
    const t = this._translate
    const diagrams: any[] = definitions.get('diagrams') || []
    const mainDiagram = diagram || diagrams[0]

    if (!mainDiagram || !mainDiagram.plane) {
      warnings.push(t('No diagram interchange (DI) found; elements without position are not displayed'))
      return { warnings }
    }

    const walker = new PlaneWalker(this, warnings, t)
    walker.walkPlane(mainDiagram.plane, true)

    // Zusätzliche Ebenen für zugeklappte Teilprozesse (Drill-down).
    for (const other of diagrams) {
      if (other === mainDiagram || !other.plane) continue
      const bo = other.plane.bpmnElement
      if (bo && is(bo, 'bpmn:SubProcess')) {
        new PlaneWalker(this, warnings, t).walkPlane(other.plane, false)
      } else {
        warnings.push(t('Additional diagram {id} is kept but not displayed', { id: other.id || '?' }))
      }
    }
    return { warnings }
  }

  createRoot(bo: any, plane: any, isMain: boolean): any {
    const id = isMain ? bo.id : `${bo.id}_plane`
    const root = this._elementFactory.createRoot({ id, businessObject: bo, di: plane })
    if (isMain) {
      this._canvas.setRootElement(root)
    } else {
      this._canvas.addRootElement(root)
    }
    return root
  }

  addShape(bo: any, di: any, parent: any, extra: Record<string, any> = {}): any {
    const bounds = di.bounds || { x: 0, y: 0, width: 0, height: 0 }
    const collapsed = is(bo, 'bpmn:SubProcess') ? !isExpanded(bo, di) : undefined
    const shape = this._elementFactory.createShape({
      id: bo.id,
      businessObject: bo,
      di,
      x: Math.round(bounds.x),
      y: Math.round(bounds.y),
      width: Math.round(bounds.width),
      height: Math.round(bounds.height),
      ...(collapsed !== undefined ? { collapsed } : {}),
      ...extra,
    })
    if (this._elementRegistry.get(shape.id)) {
      throw new Error(this._translate('Element {id} exists more than once', { id: shape.id }))
    }
    this._canvas.addShape(shape, parent)
    this._addLabel(shape)
    this._eventBus.fire('bpmnElement.added', { element: shape })
    return shape
  }

  addConnection(bo: any, di: any, parent: any, source: any, target: any): any {
    const waypoints = (di.waypoint || []).map((point: any) => ({ x: point.x, y: point.y }))
    const connection = this._elementFactory.createConnection({
      id: bo.id,
      businessObject: bo,
      di,
      source,
      target,
      waypoints,
    })
    this._canvas.addConnection(connection, parent)
    this._addLabel(connection)
    this._eventBus.fire('bpmnElement.added', { element: connection })
    return connection
  }

  private _addLabel(element: any): void {
    const bo = element.businessObject
    if (!isLabelExternal(bo)) return
    const text = getLabel(element)
    const di = element.di
    if (!text && !(di && di.label && di.label.bounds)) return
    if (!text) return
    const bounds = getExternalLabelBounds(di, element)
    const label = this._elementFactory.createLabel({
      id: `${bo.id}_label`,
      labelTarget: element,
      type: 'label',
      businessObject: bo,
      di,
      x: Math.round(bounds.x),
      y: Math.round(bounds.y),
      width: Math.round(bounds.width),
      height: Math.round(bounds.height),
    })
    this._canvas.addShape(label, element.parent)
  }
}

/** Durchläuft eine Ebene und erzeugt die zugehörigen Diagrammelemente. */
class PlaneWalker {
  private diByElement = new Map<any, any>()
  private elements = new Map<any, any>()
  private deferredShapes: Deferred[] = []
  private deferredConnections: Deferred[] = []
  private root: any

  constructor(
    private importer: BpmnImporter,
    private warnings: string[],
    private t: (text: string, replacements?: Record<string, string>) => string,
  ) {}

  walkPlane(plane: any, isMain: boolean): void {
    for (const di of plane.get('planeElement') || []) {
      if (di.bpmnElement) this.diByElement.set(di.bpmnElement, di)
    }
    const rootBo = plane.bpmnElement
    if (!rootBo) {
      this.warnings.push(this.t('Diagram plane without BPMN element is skipped'))
      return
    }
    this.root = this.importer.createRoot(rootBo, plane, isMain)

    if (is(rootBo, 'bpmn:Collaboration')) {
      this.handleCollaboration(rootBo)
    } else if (is(rootBo, 'bpmn:Process')) {
      this.handleProcess(rootBo, this.root)
    } else if (is(rootBo, 'bpmn:SubProcess')) {
      this.handleFlowElementsContainer(rootBo, this.root)
    } else {
      this.warnings.push(this.t('Unsupported diagram root {type}', { type: rootBo.$type }))
    }

    this.deferredShapes.forEach((fn) => fn())
    this.deferredConnections.forEach((fn) => fn())
  }

  private di(bo: any): any {
    return this.diByElement.get(bo)
  }

  private warnMissing(bo: any): void {
    this.warnings.push(
      this.t('Element {id} ({type}) has no diagram information and is not displayed', {
        id: bo.id || '?',
        type: String(bo.$type).replace('bpmn:', ''),
      }),
    )
  }

  private shape(bo: any, parent: any, extra?: Record<string, any>): any {
    const di = this.di(bo)
    if (!di || !is(di, 'bpmndi:BPMNShape')) {
      this.warnMissing(bo)
      return null
    }
    try {
      const element = this.importer.addShape(bo, di, parent, extra)
      this.elements.set(bo, element)
      return element
    } catch (error) {
      this.warnings.push(String((error as Error).message || error))
      return null
    }
  }

  private connection(bo: any, parent: any, sourceBo: any, targetBo: any): void {
    const di = this.di(bo)
    if (!di || !is(di, 'bpmndi:BPMNEdge')) {
      this.warnMissing(bo)
      return
    }
    const source = this.elements.get(sourceBo)
    const target = this.elements.get(targetBo)
    if (!source || !target) {
      this.warnings.push(
        this.t('Connection {id} is not displayed: source or target is missing', { id: bo.id || '?' }),
      )
      return
    }
    try {
      const element = this.importer.addConnection(bo, di, parent, source, target)
      this.elements.set(bo, element)
    } catch (error) {
      this.warnings.push(String((error as Error).message || error))
    }
  }

  private handleCollaboration(collaboration: any): void {
    for (const participant of collaboration.get('participants')) {
      const shape = this.shape(participant, this.root)
      const process = participant.processRef
      if (process) this.handleProcess(process, shape || this.root)
    }
    this.handleArtifacts(collaboration, this.root)
    for (const messageFlow of collaboration.get('messageFlows')) {
      this.deferredConnections.push(() =>
        this.connection(messageFlow, this.root, messageFlow.sourceRef, messageFlow.targetRef),
      )
    }
  }

  private handleProcess(process: any, parent: any): void {
    for (const laneSet of process.get('laneSets')) this.handleLaneSet(laneSet, parent)
    this.handleFlowElementsContainer(process, parent)
    const io = process.ioSpecification
    if (io) {
      for (const input of io.get('dataInputs')) {
        if (this.di(input)) this.shape(input, parent)
      }
      for (const output of io.get('dataOutputs')) {
        if (this.di(output)) this.shape(output, parent)
      }
    }
  }

  private handleLaneSet(laneSet: any, parent: any): void {
    for (const lane of laneSet.get('lanes')) {
      this.shape(lane, parent)
      if (lane.childLaneSet) this.handleLaneSet(lane.childLaneSet, parent)
    }
  }

  private handleFlowElementsContainer(container: any, parent: any): void {
    const flowElements: any[] = container.get('flowElements') || []
    for (const element of flowElements) {
      if (is(element, 'bpmn:SequenceFlow')) {
        this.deferredConnections.push(() => this.connection(element, parent, element.sourceRef, element.targetRef))
      } else if (is(element, 'bpmn:BoundaryEvent')) {
        this.deferredShapes.push(() => {
          const host = this.elements.get(element.attachedToRef)
          if (!host) {
            this.warnings.push(this.t('Boundary event {id} has no displayed host', { id: element.id || '?' }))
            return
          }
          const shape = this.shape(element, host.parent, { host })
          if (shape) this.handleDataAssociations(element, parent)
        })
      } else if (is(element, 'bpmn:DataObject')) {
        // rein semantisch, keine Form
      } else if (is(element, 'bpmn:FlowNode') || is(element, 'bpmn:DataObjectReference') || is(element, 'bpmn:DataStoreReference')) {
        const shape = this.shape(element, parent)
        if (shape && is(element, 'bpmn:SubProcess') && isExpanded(element, shape.di)) {
          this.handleFlowElementsContainer(element, shape)
        }
        if (shape) this.handleDataAssociations(element, parent)
      } else if (this.di(element)) {
        this.shape(element, parent)
      }
    }
    this.handleArtifacts(container, parent)
  }

  private handleDataAssociations(element: any, parent: any): void {
    for (const association of element.get('dataInputAssociations') || []) {
      const source = (association.get('sourceRef') || [])[0]
      this.deferredConnections.push(() => this.connection(association, this.connectionParent(parent), source, element))
    }
    for (const association of element.get('dataOutputAssociations') || []) {
      this.deferredConnections.push(() =>
        this.connection(association, this.connectionParent(parent), element, association.targetRef),
      )
    }
  }

  private connectionParent(parent: any): any {
    return parent || this.root
  }

  private handleArtifacts(container: any, parent: any): void {
    const artifacts: any[] = container.get('artifacts') || []
    for (const artifact of artifacts) {
      if (is(artifact, 'bpmn:Association')) {
        this.deferredConnections.push(() => this.connection(artifact, parent, artifact.sourceRef, artifact.targetRef))
      } else {
        this.shape(artifact, parent)
      }
    }
  }
}

export default BpmnImporter
