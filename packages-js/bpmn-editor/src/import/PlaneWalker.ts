/**
 * Durchläuft eine Ebene (`bpmndi:BPMNPlane`) und erzeugt die zugehörigen
 * Diagrammelemente. Kanten und Randereignisse werden zurückgestellt, bis
 * alle Formen existieren.
 */

import { is, isExpanded } from '../util/ModelUtil'
import type { BpmnElement, ModdleElement } from '../types'
import type { BpmnImporter } from './Importer'

type Deferred = () => void

export default class PlaneWalker {
  private readonly diByElement = new Map<ModdleElement, ModdleElement>()
  private readonly elements = new Map<ModdleElement, BpmnElement>()
  private readonly deferredShapes: Deferred[] = []
  private readonly deferredConnections: Deferred[] = []
  private root: BpmnElement | undefined

  constructor(
    private readonly importer: BpmnImporter,
    private readonly warnings: string[],
  ) {}

  private t(text: string, replacements?: Record<string, unknown>): string {
    return this.importer.translate(text, replacements)
  }

  walk(plane: ModdleElement, isMain: boolean): void {
    for (const di of plane.get<ModdleElement[]>('planeElement') || []) {
      if (di.bpmnElement) this.diByElement.set(di.bpmnElement, di)
    }
    const rootBo = plane.bpmnElement
    if (!rootBo) {
      this.warnings.push(this.t('Diagram plane without BPMN element is skipped'))
      return
    }
    const root = this.importer.createRoot(rootBo, plane, isMain)
    this.root = root
    if (is(rootBo, 'bpmn:Collaboration')) this.handleCollaboration(rootBo, root)
    else if (is(rootBo, 'bpmn:Process')) this.handleProcess(rootBo, root)
    else if (is(rootBo, 'bpmn:SubProcess')) this.handleContainer(rootBo, root)
    else this.warnings.push(this.t('Unsupported diagram root {type}', { type: rootBo.$type }))
    this.deferredShapes.forEach((run) => run())
    this.deferredConnections.forEach((run) => run())
  }

  private warnMissing(bo: ModdleElement): void {
    this.warnings.push(
      this.t('Element {id} ({type}) has no diagram information and is not displayed', {
        id: bo.id || '?',
        type: bo.$type.replace('bpmn:', ''),
      }),
    )
  }

  private attempt<T>(run: () => T): T | undefined {
    try {
      return run()
    } catch (error) {
      this.warnings.push(String((error as Error).message || error))
      return undefined
    }
  }

  private shape(bo: ModdleElement, parent: BpmnElement, extra?: Record<string, unknown>): BpmnElement | undefined {
    const di = this.diByElement.get(bo)
    if (!di || !is(di, 'bpmndi:BPMNShape')) {
      this.warnMissing(bo)
      return undefined
    }
    const element = this.attempt(() => this.importer.addShape(bo, di, parent, extra))
    if (element) this.elements.set(bo, element)
    return element
  }

  private connection(bo: ModdleElement, parent: BpmnElement, sourceBo: ModdleElement | undefined, targetBo: ModdleElement | undefined): void {
    const di = this.diByElement.get(bo)
    if (!di || !is(di, 'bpmndi:BPMNEdge')) {
      this.warnMissing(bo)
      return
    }
    const source = sourceBo && this.elements.get(sourceBo)
    const target = targetBo && this.elements.get(targetBo)
    if (!source || !target) {
      this.warnings.push(this.t('Connection {id} is not displayed: source or target is missing', { id: bo.id || '?' }))
      return
    }
    const element = this.attempt(() => this.importer.addConnection(bo, di, parent, source, target))
    if (element) this.elements.set(bo, element)
  }

  private deferConnection(bo: ModdleElement, parent: BpmnElement, source: ModdleElement | undefined, target: ModdleElement | undefined): void {
    this.deferredConnections.push(() => this.connection(bo, parent, source, target))
  }

  private handleCollaboration(collaboration: ModdleElement, root: BpmnElement): void {
    for (const participant of collaboration.get<ModdleElement[]>('participants')) {
      const shape = this.shape(participant, root)
      if (participant.processRef) this.handleProcess(participant.processRef, shape || root)
    }
    this.handleArtifacts(collaboration, root)
    for (const flow of collaboration.get<ModdleElement[]>('messageFlows')) this.deferConnection(flow, root, flow.sourceRef, flow.targetRef)
  }

  private handleProcess(process: ModdleElement, parent: BpmnElement): void {
    for (const laneSet of process.get<ModdleElement[]>('laneSets')) this.handleLaneSet(laneSet, parent)
    this.handleContainer(process, parent)
    const io = process.ioSpecification
    const ioElements = io ? [...io.get<ModdleElement[]>('dataInputs'), ...io.get<ModdleElement[]>('dataOutputs')] : []
    for (const element of ioElements) {
      if (this.diByElement.has(element)) this.shape(element, parent)
    }
  }

  private handleLaneSet(laneSet: ModdleElement, parent: BpmnElement): void {
    for (const lane of laneSet.get<ModdleElement[]>('lanes')) {
      this.shape(lane, parent)
      if (lane.childLaneSet) this.handleLaneSet(lane.childLaneSet, parent)
    }
  }

  private handleContainer(container: ModdleElement, parent: BpmnElement): void {
    for (const element of container.get<ModdleElement[]>('flowElements') || []) this.handleFlowElement(element, parent)
    this.handleArtifacts(container, parent)
  }

  private handleFlowElement(element: ModdleElement, parent: BpmnElement): void {
    if (is(element, 'bpmn:SequenceFlow')) this.deferConnection(element, parent, element.sourceRef, element.targetRef)
    else if (is(element, 'bpmn:BoundaryEvent')) this.deferredShapes.push(() => this.handleBoundaryEvent(element, parent))
    else if (is(element, 'bpmn:DataObject')) return
    else if (this.diByElement.has(element) || is(element, 'bpmn:FlowNode') || is(element, 'bpmn:ItemAwareElement')) this.handleNode(element, parent)
  }

  private handleNode(element: ModdleElement, parent: BpmnElement): void {
    const shape = this.shape(element, parent)
    if (!shape) return
    if (is(element, 'bpmn:SubProcess') && isExpanded(element, shape.di)) this.handleContainer(element, shape)
    this.handleDataAssociations(element, parent)
  }

  private handleBoundaryEvent(element: ModdleElement, parent: BpmnElement): void {
    const host = element.attachedToRef && this.elements.get(element.attachedToRef)
    if (!host) {
      this.warnings.push(this.t('Boundary event {id} has no displayed host', { id: element.id || '?' }))
      return
    }
    if (this.shape(element, host.parent as BpmnElement, { host })) this.handleDataAssociations(element, parent)
  }

  private handleDataAssociations(element: ModdleElement, parent: BpmnElement): void {
    const target = parent || (this.root as BpmnElement)
    for (const association of element.get<ModdleElement[]>('dataInputAssociations') || []) {
      this.deferConnection(association, target, association.get<ModdleElement[]>('sourceRef')[0], element)
    }
    for (const association of element.get<ModdleElement[]>('dataOutputAssociations') || []) {
      this.deferConnection(association, target, element, association.targetRef)
    }
  }

  private handleArtifacts(container: ModdleElement, parent: BpmnElement): void {
    for (const artifact of container.get<ModdleElement[]>('artifacts') || []) {
      if (is(artifact, 'bpmn:Association')) this.deferConnection(artifact, parent, artifact.sourceRef, artifact.targetRef)
      else this.shape(artifact, parent)
    }
  }
}
