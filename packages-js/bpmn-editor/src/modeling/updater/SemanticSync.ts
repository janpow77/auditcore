/**
 * Abgleich der semantischen Einbettung (Container-Listen wie
 * `flowElements`, `artifacts`, `participants`, `laneSets`) mit dem
 * Diagrammbaum.
 */

import {
  addToList,
  getBusinessObject,
  getDefinitions,
  getList,
  is,
  isAny,
  removeFromList,
} from '../../util/ModelUtil'
import type { BpmnElement, ModdleElement } from '../../types'
import type BpmnFactory from '../BpmnFactory'

type ContainerSource = () => ModdleElement | undefined

const PROCESS_CONTENT = ['bpmn:FlowElement', 'bpmn:Artifact', 'bpmn:DataInput', 'bpmn:DataOutput', 'bpmn:Lane']

export default class SemanticSync {
  /** Merkt sich bei gelöschten Bahnen die bisherige Einbettung. */
  private readonly laneMemory = new WeakMap<ModdleElement, { laneSet: ModdleElement; index: number }>()

  constructor(
    private readonly bpmnFactory: BpmnFactory,
    private readonly definitions: ContainerSource,
  ) {}

  /** Semantischer Container zu einer Diagramm-Elternform (Bahnen zählen nicht). */
  getContainer(parentShape: BpmnElement | undefined, bo: ModdleElement): ModdleElement | undefined {
    let current: BpmnElement | undefined = parentShape
    while (current && is(current, 'bpmn:Lane')) current = current.parent as BpmnElement | undefined
    if (!current) return undefined
    const parentBo = getBusinessObject(current)
    if (is(parentBo, 'bpmn:Participant') && isAny(bo, PROCESS_CONTENT)) return this.ensureProcess(parentBo)
    return parentBo
  }

  /** Pools ohne Prozess (z. B. nach Ersetzen) erhalten bei Bedarf einen. */
  ensureProcess(participant: ModdleElement): ModdleElement {
    if (participant.processRef) return participant.processRef
    const process = this.bpmnFactory.create('bpmn:Process', { isExecutable: false })
    participant.processRef = process
    const definitions = getDefinitions(participant) || this.definitions()
    if (definitions) {
      process.$parent = definitions
      addToList(definitions.get<ModdleElement[]>('rootElements'), process)
    }
    return process
  }

  /** Aktualisiert die Einbettung einer Form. */
  update(shape: BpmnElement): void {
    const bo = getBusinessObject(shape)
    if (is(bo, 'bpmn:Lane')) return this.updateLane(shape)
    const container = shape.parent ? this.getContainer(shape.parent as BpmnElement, bo) : undefined
    if (is(bo, 'bpmn:Participant')) return this.updateParticipant(bo, container)
    if (isAny(bo, ['bpmn:DataInput', 'bpmn:DataOutput'])) return this.updateDataIo(bo, container)
    const property = is(bo, 'bpmn:FlowElement') ? 'flowElements' : is(bo, 'bpmn:Artifact') ? 'artifacts' : null
    if (!property) return
    this.moveTo(bo, container, property)
    if (is(bo, 'bpmn:DataObjectReference') && bo.dataObjectRef) this.moveDataObject(bo.dataObjectRef, container)
    if (is(bo, 'bpmn:Group')) this.updateGroupCategory(bo, !!container)
  }

  /** Verschiebt ein moddle-Element in die Liste `property` des Containers. */
  moveTo(bo: ModdleElement, container: ModdleElement | undefined, property: string): void {
    const oldContainer = bo.$parent || undefined
    if (oldContainer && oldContainer !== container) removeFromList(getList(oldContainer, property), bo)
    const list = getList(container, property)
    if (container && list) {
      addToList(list, bo)
      bo.$parent = container
    } else if (!container) {
      if (oldContainer) removeFromList(getList(oldContainer, property), bo)
      bo.$parent = null
    }
  }

  /** Datenobjekt wandert mit der Referenz, solange keine andere Referenz es nutzt. */
  private moveDataObject(dataObject: ModdleElement, container: ModdleElement | undefined): void {
    const oldContainer = dataObject.$parent || undefined
    if (oldContainer === container) {
      if (container) addToList(container.get<ModdleElement[]>('flowElements'), dataObject)
      return
    }
    const stillUsed = (getList(oldContainer, 'flowElements') || []).some(
      (element) => is(element, 'bpmn:DataObjectReference') && element.dataObjectRef === dataObject,
    )
    if (stillUsed && !container) return
    if (!stillUsed && oldContainer) removeFromList(getList(oldContainer, 'flowElements'), dataObject)
    if (container) {
      addToList(container.get<ModdleElement[]>('flowElements'), dataObject)
      dataObject.$parent = container
    }
  }

  private updateGroupCategory(group: ModdleElement, present: boolean): void {
    const value = group.categoryValueRef
    const category = value?.$parent
    const definitions = this.definitions()
    if (!value || !category || !definitions) return
    const rootElements = definitions.get<ModdleElement[]>('rootElements')
    if (present) {
      category.$parent = definitions
      addToList(rootElements, category)
      addToList(category.get<ModdleElement[]>('categoryValue'), value)
      return
    }
    removeFromList(category.get<ModdleElement[]>('categoryValue'), value)
    if (category.get<ModdleElement[]>('categoryValue').length === 0) removeFromList(rootElements, category)
  }

  private updateParticipant(bo: ModdleElement, collaboration: ModdleElement | undefined): void {
    const old = bo.$parent || undefined
    if (old && old !== collaboration) removeFromList(getList(old, 'participants'), bo)
    if (collaboration && is(collaboration, 'bpmn:Collaboration')) {
      addToList(collaboration.get<ModdleElement[]>('participants'), bo)
      bo.$parent = collaboration
      this.setProcessRegistered(bo, true)
      return
    }
    bo.$parent = null
    const stillUsed = (getList(old, 'participants') || []).some((other) => other.processRef === bo.processRef)
    if (!stillUsed) this.setProcessRegistered(bo, false)
  }

  /** Nimmt den Prozess eines Pools in die Wurzelelemente auf bzw. entfernt ihn. */
  private setProcessRegistered(participant: ModdleElement, registered: boolean): void {
    const process = participant.processRef
    const definitions = this.definitions() || getDefinitions(participant)
    if (!process || !definitions) return
    const rootElements = definitions.get<ModdleElement[]>('rootElements')
    if (!registered) {
      removeFromList(rootElements, process)
      return
    }
    process.$parent = definitions
    addToList(rootElements, process)
  }

  private updateDataIo(bo: ModdleElement, process: ModdleElement | undefined): void {
    const property = is(bo, 'bpmn:DataInput') ? 'dataInputs' : 'dataOutputs'
    const oldSpec = bo.$parent || undefined
    if (oldSpec && is(oldSpec, 'bpmn:InputOutputSpecification')) {
      if (process && process.ioSpecification === oldSpec) return
      removeFromList(oldSpec.get<ModdleElement[]>(property), bo)
    }
    if (!process) {
      bo.$parent = null
      return
    }
    const spec = process.ioSpecification || this.createIoSpecification(process)
    addToList(spec.get<ModdleElement[]>(property), bo)
    bo.$parent = spec
  }

  private createIoSpecification(process: ModdleElement): ModdleElement {
    const inputSet = this.bpmnFactory.create('bpmn:InputSet')
    const outputSet = this.bpmnFactory.create('bpmn:OutputSet')
    const spec = this.bpmnFactory.create('bpmn:InputOutputSpecification', { inputSets: [inputSet], outputSets: [outputSet] })
    inputSet.$parent = spec
    outputSet.$parent = spec
    spec.$parent = process
    process.ioSpecification = spec
    return spec
  }

  /** Bahnen: Einbettung bleibt beim Löschen gemerkt, damit Rückgängig sie wiederherstellt. */
  private updateLane(shape: BpmnElement): void {
    const bo = getBusinessObject(shape)
    const laneSet = bo.$parent && is(bo.$parent, 'bpmn:LaneSet') ? bo.$parent : undefined
    if (!shape.parent) {
      if (laneSet) this.laneMemory.set(bo, { laneSet, index: removeFromList(laneSet.get<ModdleElement[]>('lanes'), bo) })
      return
    }
    const memory = this.laneMemory.get(bo)
    if (memory) {
      addToList(memory.laneSet.get<ModdleElement[]>('lanes'), bo, memory.index)
      bo.$parent = memory.laneSet
      this.laneMemory.delete(bo)
      return
    }
    if (laneSet) {
      addToList(laneSet.get<ModdleElement[]>('lanes'), bo)
      return
    }
    this.addToProcessLaneSet(shape, bo)
  }

  private addToProcessLaneSet(shape: BpmnElement, bo: ModdleElement): void {
    const process = this.getContainer(shape.parent as BpmnElement, bo)
    if (!process || !is(process, 'bpmn:Process')) return
    const laneSets = process.get<ModdleElement[]>('laneSets')
    let laneSet = laneSets[0]
    if (!laneSet) {
      laneSet = this.bpmnFactory.create('bpmn:LaneSet')
      laneSet.$parent = process
      laneSets.push(laneSet)
    }
    addToList(laneSet.get<ModdleElement[]>('lanes'), bo)
    bo.$parent = laneSet
  }
}
