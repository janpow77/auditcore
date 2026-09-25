/**
 * Hält semantisches Modell (moddle) und DI synchron zum Diagramm.
 *
 * Grundsatz: Das Diagramm (Eltern, Quelle/Ziel, Lage) ist nach jedem
 * ausgeführten oder zurückgenommenen Befehl maßgeblich. Der Updater leitet
 * daraus Container, Referenzen und DI ab. Dadurch funktionieren Rückgängig
 * und Wiederholen ohne gesonderte Gegenlogik.
 */

import CommandInterceptor from 'diagram-js/lib/command/CommandInterceptor'

import {
  addToList,
  getBusinessObject,
  getDefinitions,
  is,
  isAny,
  removeFromList,
  type DiagramElement,
} from '../util/ModelUtil'

/* eslint-disable @typescript-eslint/no-explicit-any */

const SHAPE_COMMANDS = [
  'shape.create',
  'shape.delete',
  'shape.move',
  'shape.resize',
  'shape.toggleCollapse',
  'element.updateAttachment',
]

const CONNECTION_COMMANDS = [
  'connection.create',
  'connection.delete',
  'connection.move',
  'connection.reconnect',
  'connection.layout',
  'connection.updateWaypoints',
]

export default class BpmnUpdater extends (CommandInterceptor as any) {
  static $inject = ['eventBus', 'bpmnFactory', 'canvas', 'elementRegistry']

  _bpmnFactory: any
  _canvas: any
  _elementRegistry: any
  /** Merkt sich bei gelöschten Bahnen die bisherige Einbettung. */
  _laneMemory = new WeakMap<any, { laneSet: any; index: number }>()

  constructor(eventBus: any, bpmnFactory: any, canvas: any, elementRegistry: any) {
    super(eventBus)
    this._bpmnFactory = bpmnFactory
    this._canvas = canvas
    this._elementRegistry = elementRegistry

    const syncShape = (event: any) => {
      const context = event.context
      const shape = context.shape || context.element
      if (!shape) return
      this.updateShape(shape)
      if (context.newHost !== undefined || context.oldHost !== undefined) this.updateAttachment(shape)
    }
    this.executed(SHAPE_COMMANDS, syncShape)
    this.reverted(SHAPE_COMMANDS, syncShape)

    const syncConnection = (event: any) => {
      const connection = event.context.connection
      if (connection) this.updateConnectionFull(connection)
    }
    this.executed(CONNECTION_COMMANDS, syncConnection)
    this.reverted(CONNECTION_COMMANDS, syncConnection)

    const syncLabel = (event: any) => {
      const context = event.context
      const label = context.shape || context.labelTarget?.label
      if (label && label.labelTarget) this.updateLabelDi(label)
    }
    this.executed(['label.create'], syncLabel)
    this.reverted(['label.create'], (event: any) => {
      const context = event.context
      const target = context.labelTarget
      if (target && target.di && !target.label) target.di.label = undefined
    })

    // Größenänderung durch Raumwerkzeug: alle betroffenen Formen synchronisieren.
    const syncSpace = (event: any) => {
      const context = event.context
      ;(context.movingShapes || []).forEach((shape: any) => this.updateShape(shape))
      ;(context.resizingShapes || []).forEach((shape: any) => this.updateShape(shape))
    }
    this.executed(['spaceTool'], syncSpace)
    this.reverted(['spaceTool'], syncSpace)

    // Beim Anhängen an ein anderes Element wird ein Randereignis zum Zwischenereignis und umgekehrt.
    eventBus.on('commandStack.shape.attach.executed', (event: any) => this.updateAttachment(event.context.shape))
  }

  // -------------------------------------------------------------------------
  // Formen
  // -------------------------------------------------------------------------

  updateShape(shape: DiagramElement): void {
    if (shape.labelTarget) {
      if (shape.parent) {
        this.updateLabelDi(shape)
      } else if (shape.labelTarget.di && shape.labelTarget.label !== shape) {
        // Beschriftung gelöscht, Ziel besteht fort.
        shape.labelTarget.di.label = undefined
      }
      return
    }
    if (shape.waypoints) {
      this.updateConnectionFull(shape)
      return
    }
    if (!shape.parent && this._canvas.getRootElements().includes(shape)) return
    this.updateSemanticParent(shape)
    this.updateDiParent(shape)
    this.updateBounds(shape)
    if (shape.label && shape.label.parent) this.updateLabelDi(shape.label)
  }

  updateBounds(shape: DiagramElement): void {
    const di = shape.di
    if (!di || !is(di, 'bpmndi:BPMNShape')) return
    const bounds = { x: shape.x, y: shape.y, width: shape.width, height: shape.height }
    if (!di.bounds) {
      di.bounds = this._bpmnFactory.createDiBounds(bounds)
    } else {
      di.bounds.x = Math.round(bounds.x)
      di.bounds.y = Math.round(bounds.y)
      di.bounds.width = Math.round(bounds.width)
      di.bounds.height = Math.round(bounds.height)
    }
  }

  updateLabelDi(label: DiagramElement): void {
    const target = label.labelTarget
    const di = target && target.di
    if (!di) return
    if (!di.label) {
      di.label = this._bpmnFactory.createDiLabel()
      di.label.$parent = di
    }
    const bounds = { x: label.x, y: label.y, width: label.width, height: label.height }
    if (!di.label.bounds) {
      di.label.bounds = this._bpmnFactory.createDiBounds(bounds)
    } else {
      di.label.bounds.x = Math.round(bounds.x)
      di.label.bounds.y = Math.round(bounds.y)
      di.label.bounds.width = Math.round(bounds.width)
      di.label.bounds.height = Math.round(bounds.height)
    }
  }

  updateAttachment(shape: DiagramElement): void {
    const bo = getBusinessObject(shape)
    if (!is(bo, 'bpmn:BoundaryEvent')) return
    bo.attachedToRef = shape.host ? getBusinessObject(shape.host) : undefined
  }

  /** Ermittelt das semantische Elternobjekt zu einer Diagramm-Elternform. */
  getSemanticContainer(parentShape: DiagramElement, bo: any): any {
    if (!parentShape) return null
    let parentBo = getBusinessObject(parentShape)

    if (is(parentBo, 'bpmn:Lane')) {
      // Bahnen sind keine Container; maßgeblich ist der Pool bzw. Prozess.
      let current = parentShape.parent
      while (current && is(current, 'bpmn:Lane')) current = current.parent
      parentBo = current ? getBusinessObject(current) : null
    }

    if (is(parentBo, 'bpmn:Participant')) {
      if (isAny(bo, ['bpmn:FlowElement', 'bpmn:Artifact', 'bpmn:DataInput', 'bpmn:DataOutput']) || is(bo, 'bpmn:Lane')) {
        return this.ensureProcess(parentBo)
      }
      return parentBo
    }
    return parentBo
  }

  /** Pools ohne Prozess (z. B. nach Ersetzen) erhalten bei Bedarf einen. */
  ensureProcess(participantBo: any): any {
    if (!participantBo.processRef) {
      const process = this._bpmnFactory.create('bpmn:Process', { isExecutable: false })
      participantBo.processRef = process
      const definitions = getDefinitions(participantBo)
      if (definitions) {
        process.$parent = definitions
        addToList(definitions.get('rootElements'), process)
      }
    }
    return participantBo.processRef
  }

  updateSemanticParent(shape: DiagramElement): void {
    const bo = getBusinessObject(shape)
    const parentShape = shape.parent

    if (is(bo, 'bpmn:Lane')) {
      this.updateLaneParent(shape)
      return
    }

    const container = parentShape ? this.getSemanticContainer(parentShape, bo) : null

    if (is(bo, 'bpmn:Participant')) {
      this.updateParticipant(bo, container)
      return
    }

    if (isAny(bo, ['bpmn:DataInput', 'bpmn:DataOutput'])) {
      this.updateDataIo(bo, container)
      return
    }

    let property: string | null = null
    if (is(bo, 'bpmn:FlowElement')) property = 'flowElements'
    else if (is(bo, 'bpmn:Artifact')) property = 'artifacts'
    if (!property) return

    this.moveToContainer(bo, container, property)

    if (is(bo, 'bpmn:DataObjectReference') && bo.dataObjectRef) {
      this.moveToContainer(bo.dataObjectRef, container, 'flowElements', true)
    }
    if (is(bo, 'bpmn:Group')) this.updateGroupCategory(bo, !!container)
  }

  /** Verschiebt ein moddle-Element in die Liste `property` des Containers. */
  moveToContainer(bo: any, container: any, property: string, keepIfShared = false): void {
    const oldContainer = bo.$parent
    if (oldContainer === container && container && container.get(property).includes(bo)) return

    if (oldContainer && oldContainer !== container && typeof oldContainer.get === 'function') {
      const list = safeList(oldContainer, property)
      if (list) {
        if (keepIfShared && isStillReferenced(bo, oldContainer)) {
          // Datenobjekt wird noch von einer anderen Referenz im alten Container genutzt.
        } else {
          removeFromList(list, bo)
        }
      }
    }
    if (container) {
      const list = safeList(container, property)
      if (list) {
        addToList(list, bo)
        bo.$parent = container
      }
    } else if (!keepIfShared || !isStillReferenced(bo, oldContainer)) {
      bo.$parent = null
      if (oldContainer) removeFromList(safeList(oldContainer, property), bo)
    }
  }

  updateGroupCategory(group: any, present: boolean): void {
    const value = group.categoryValueRef
    if (!value) return
    const category = value.$parent
    const definitions = this._definitions()
    if (!category || !definitions) return
    if (present) {
      if (!definitions.get('rootElements').includes(category)) {
        category.$parent = definitions
        definitions.get('rootElements').push(category)
      }
      addToList(category.get('categoryValue'), value)
    } else {
      // Nur entfernen, wenn keine andere Gruppe denselben Wert nutzt.
      const others = this._elementRegistry.filter(
        (element: any) => is(element, 'bpmn:Group') && element.parent && getBusinessObject(element) !== group,
      )
      const shared = others.some((other: any) => getBusinessObject(other).categoryValueRef === value)
      if (!shared) {
        removeFromList(category.get('categoryValue'), value)
        if (category.get('categoryValue').length === 0) removeFromList(definitions.get('rootElements'), category)
      }
    }
  }

  updateParticipant(bo: any, collaboration: any): void {
    const definitions = this._definitions() || getDefinitions(bo)
    const old = bo.$parent
    if (old && old !== collaboration) removeFromList(safeList(old, 'participants'), bo)
    if (collaboration && is(collaboration, 'bpmn:Collaboration')) {
      addToList(collaboration.get('participants'), bo)
      bo.$parent = collaboration
      if (bo.processRef && definitions) {
        bo.processRef.$parent = definitions
        addToList(definitions.get('rootElements'), bo.processRef)
      }
    } else {
      const oldCollaboration = old && is(old, 'bpmn:Collaboration') ? old : null
      bo.$parent = null
      const stillUsed =
        !!oldCollaboration &&
        oldCollaboration.get('participants').some((other: any) => other !== bo && other.processRef === bo.processRef)
      if (bo.processRef && definitions && !stillUsed) {
        removeFromList(definitions.get('rootElements'), bo.processRef)
      }
    }
  }

  updateDataIo(bo: any, process: any): void {
    const property = is(bo, 'bpmn:DataInput') ? 'dataInputs' : 'dataOutputs'
    const oldSpec = bo.$parent
    if (oldSpec && is(oldSpec, 'bpmn:InputOutputSpecification')) {
      if (process && process.ioSpecification === oldSpec) return
      removeFromList(oldSpec.get(property), bo)
    }
    if (!process) {
      bo.$parent = null
      return
    }
    let spec = process.ioSpecification
    if (!spec) {
      spec = this._bpmnFactory.create('bpmn:InputOutputSpecification', {
        inputSets: [this._bpmnFactory.create('bpmn:InputSet')],
        outputSets: [this._bpmnFactory.create('bpmn:OutputSet')],
      })
      spec.inputSets.forEach((set: any) => (set.$parent = spec))
      spec.outputSets.forEach((set: any) => (set.$parent = spec))
      spec.$parent = process
      process.ioSpecification = spec
    }
    addToList(spec.get(property), bo)
    bo.$parent = spec
  }

  /** Bahnen: Einbettung bleibt beim Löschen erhalten, damit Rückgängig sie wiederherstellt. */
  updateLaneParent(shape: DiagramElement): void {
    const bo = getBusinessObject(shape)
    if (!shape.parent) {
      const laneSet = bo.$parent
      if (laneSet && is(laneSet, 'bpmn:LaneSet')) {
        const index = removeFromList(laneSet.get('lanes'), bo)
        this._laneMemory.set(bo, { laneSet, index })
      }
      return
    }
    const memory = this._laneMemory.get(bo)
    if (memory && !memory.laneSet.get('lanes').includes(bo)) {
      addToList(memory.laneSet.get('lanes'), bo, memory.index)
      bo.$parent = memory.laneSet
      this._laneMemory.delete(bo)
      return
    }
    if (bo.$parent && is(bo.$parent, 'bpmn:LaneSet')) {
      addToList(bo.$parent.get('lanes'), bo)
      return
    }
    // Neue Bahn ohne Vorgabe: in die Bahnmenge des Prozesses.
    const process = this.getSemanticContainer(shape.parent, bo)
    if (!process || !is(process, 'bpmn:Process')) return
    let laneSet = process.get('laneSets')[0]
    if (!laneSet) {
      laneSet = this._bpmnFactory.create('bpmn:LaneSet')
      laneSet.$parent = process
      process.get('laneSets').push(laneSet)
    }
    addToList(laneSet.get('lanes'), bo)
    bo.$parent = laneSet
  }

  // -------------------------------------------------------------------------
  // DI-Einbettung
  // -------------------------------------------------------------------------

  getPlane(element: DiagramElement): any {
    let current = element
    while (current && current.parent) current = current.parent
    if (!current) return null
    const di = current.di
    return di && is(di, 'bpmndi:BPMNPlane') ? di : null
  }

  updateDiParent(element: DiagramElement): void {
    const di = element.di
    if (!di || is(di, 'bpmndi:BPMNPlane')) return
    const plane = element.parent ? this.getPlane(element) : null
    const oldPlane = di.$parent
    if (oldPlane && oldPlane !== plane) removeFromList(oldPlane.get('planeElement'), di)
    if (plane) {
      addToList(plane.get('planeElement'), di)
      di.$parent = plane
    } else {
      di.$parent = null
    }
  }

  // -------------------------------------------------------------------------
  // Kanten
  // -------------------------------------------------------------------------

  updateConnectionFull(connection: DiagramElement): void {
    this.updateConnection(connection)
    this.updateDiParent(connection)
    this.updateWaypoints(connection)
    if (connection.label && connection.label.parent) this.updateLabelDi(connection.label)
  }

  updateWaypoints(connection: DiagramElement): void {
    const di = connection.di
    if (!di || !connection.waypoints) return
    di.waypoint = this._bpmnFactory.createDiWaypoints(connection.waypoints)
    di.waypoint.forEach((point: any) => (point.$parent = di))
  }

  updateConnection(connection: DiagramElement): void {
    const bo = getBusinessObject(connection)
    const attached = !!connection.parent
    const source = connection.source ? getBusinessObject(connection.source) : null
    const target = connection.target ? getBusinessObject(connection.target) : null

    if (is(bo, 'bpmn:DataInputAssociation') || is(bo, 'bpmn:DataOutputAssociation')) {
      this.updateDataAssociation(connection, bo, attached, source, target)
      return
    }

    if (is(bo, 'bpmn:SequenceFlow')) {
      if (bo.sourceRef && (bo.sourceRef !== source || !attached)) removeFromList(bo.sourceRef.get('outgoing'), bo)
      if (bo.targetRef && (bo.targetRef !== target || !attached)) removeFromList(bo.targetRef.get('incoming'), bo)
      if (attached) {
        if (source) {
          bo.sourceRef = source
          addToList(source.get('outgoing'), bo)
        }
        if (target) {
          bo.targetRef = target
          addToList(target.get('incoming'), bo)
        }
      }
    } else if (attached) {
      if (source) bo.sourceRef = source
      if (target) bo.targetRef = target
    }

    // Container
    if (is(bo, 'bpmn:MessageFlow')) {
      const collaboration = attached ? this._rootBo(connection) : null
      if (bo.$parent && bo.$parent !== collaboration) removeFromList(safeList(bo.$parent, 'messageFlows'), bo)
      if (collaboration && is(collaboration, 'bpmn:Collaboration')) {
        addToList(collaboration.get('messageFlows'), bo)
        bo.$parent = collaboration
      } else if (!attached) {
        bo.$parent = null
      }
    } else if (is(bo, 'bpmn:SequenceFlow')) {
      const container = attached ? this.getSemanticContainer(connection.parent, bo) : null
      this.moveToContainer(bo, container, 'flowElements')
    } else if (is(bo, 'bpmn:Association')) {
      const container = attached ? this.getSemanticContainer(connection.parent, bo) : null
      this.moveToContainer(bo, container, 'artifacts')
    }
  }

  updateDataAssociation(connection: DiagramElement, bo: any, attached: boolean, source: any, target: any): void {
    const isInput = is(bo, 'bpmn:DataInputAssociation')
    const property = isInput ? 'dataInputAssociations' : 'dataOutputAssociations'
    const owner = attached ? (isInput ? target : source) : null
    const oldOwner = bo.$parent
    if (oldOwner && oldOwner !== owner) removeFromList(safeList(oldOwner, property), bo)
    if (!owner) {
      bo.$parent = null
      return
    }
    addToList(owner.get(property), bo)
    bo.$parent = owner
    if (isInput) {
      const refs = bo.get('sourceRef')
      refs.length = 0
      if (source) refs.push(source)
      if (!bo.targetRef && is(owner, 'bpmn:Activity')) {
        const property = this._bpmnFactory.create('bpmn:Property')
        property.$parent = owner
        owner.get('properties').push(property)
        bo.targetRef = property
      }
    } else {
      bo.targetRef = target
    }
  }

  private _rootBo(element: DiagramElement): any {
    let current = element
    while (current && current.parent) current = current.parent
    return current ? getBusinessObject(current) : null
  }

  private _definitions(): any {
    const root = this._canvas.getRootElement && this._canvas.getRootElements()[0]
    return root ? getDefinitions(getBusinessObject(root)) : null
  }
}

function safeList(container: any, property: string): any[] | undefined {
  if (!container || typeof container.get !== 'function') return undefined
  try {
    const descriptor = container.$descriptor
    if (descriptor && !descriptor.propertiesByName?.[property]) return undefined
    return container.get(property)
  } catch {
    return undefined
  }
}

function isStillReferenced(dataObject: any, container: any): boolean {
  if (!container) return false
  const elements = safeList(container, 'flowElements') || []
  return elements.some((element: any) => is(element, 'bpmn:DataObjectReference') && element.dataObjectRef === dataObject && element.$parent === container)
}
