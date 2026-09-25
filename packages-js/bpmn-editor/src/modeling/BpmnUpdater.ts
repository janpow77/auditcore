/**
 * Hält semantisches Modell (moddle) und DI synchron zum Diagramm.
 *
 * Grundsatz: Das Diagramm (Eltern, Quelle/Ziel, Lage) ist nach jedem
 * ausgeführten oder zurückgenommenen Befehl maßgeblich. Der Updater leitet
 * daraus Container, Referenzen und DI ab. Dadurch funktionieren Rückgängig
 * und Wiederholen ohne gesonderte Gegenlogik.
 */

import CommandInterceptor from 'diagram-js/lib/command/CommandInterceptor'

import { getBusinessObject, getDefinitions, is } from '../util/ModelUtil'
import type { BpmnElement, Canvas, CommandEvent, EventBus, ModdleElement } from '../types'
import type BpmnFactory from './BpmnFactory'
import ConnectionSync from './updater/ConnectionSync'
import DiSync from './updater/DiSync'
import SemanticSync from './updater/SemanticSync'

const SHAPE_COMMANDS = ['shape.create', 'shape.delete', 'shape.move', 'shape.resize', 'shape.toggleCollapse', 'element.updateAttachment']

const CONNECTION_COMMANDS = [
  'connection.create',
  'connection.delete',
  'connection.move',
  'connection.reconnect',
  'connection.layout',
  'connection.updateWaypoints',
]

interface ShapeContext {
  shape?: BpmnElement
  element?: BpmnElement
  connection?: BpmnElement
  labelTarget?: BpmnElement
  newHost?: BpmnElement
  oldHost?: BpmnElement
}

export default class BpmnUpdater extends CommandInterceptor {
  static $inject = ['eventBus', 'bpmnFactory', 'canvas']

  readonly semantic: SemanticSync
  readonly diSync: DiSync
  readonly connections: ConnectionSync

  constructor(
    eventBus: EventBus,
    bpmnFactory: BpmnFactory,
    private readonly canvas: Canvas,
  ) {
    super(eventBus)
    this.semantic = new SemanticSync(bpmnFactory, () => this.definitions())
    this.diSync = new DiSync(bpmnFactory)
    this.connections = new ConnectionSync(bpmnFactory, this.semantic)

    const syncShape = (event: CommandEvent<ShapeContext>) => {
      const context = event.context
      const shape = context.shape || context.element
      if (!shape) return
      this.updateShape(shape)
      if ('newHost' in context || 'oldHost' in context) this.updateAttachment(shape)
    }
    this.executed(SHAPE_COMMANDS, syncShape)
    this.reverted(SHAPE_COMMANDS, syncShape)

    const syncConnection = (event: CommandEvent<ShapeContext>) => {
      const connection = event.context.connection
      if (connection) this.updateConnection(connection)
    }
    this.executed(CONNECTION_COMMANDS, syncConnection)
    this.reverted(CONNECTION_COMMANDS, syncConnection)

    this.executed('label.create', (event: CommandEvent<ShapeContext>) => {
      const label = event.context.shape
      if (label?.labelTarget) this.diSync.updateLabel(label)
    })
    this.reverted('label.create', (event: CommandEvent<ShapeContext>) => {
      const target = event.context.labelTarget
      if (target && !target.label) this.diSync.removeLabel(target)
    })
  }

  /** Aktualisiert Semantik und DI einer Form (bzw. Beschriftung oder Kante). */
  updateShape(shape: BpmnElement): void {
    if (shape.labelTarget) {
      this.updateLabelShape(shape)
      return
    }
    if (shape.waypoints) {
      this.updateConnection(shape)
      return
    }
    if (!shape.parent && this.canvas.getRootElements().includes(shape as never)) return
    this.semantic.update(shape)
    this.diSync.updateParent(shape)
    this.diSync.updateBounds(shape)
    const label = shape.label as BpmnElement | undefined
    if (label && label.parent) this.diSync.updateLabel(label)
  }

  private updateLabelShape(label: BpmnElement): void {
    const target = label.labelTarget as BpmnElement
    if (label.parent) this.diSync.updateLabel(label)
    else if (target.label !== label) this.diSync.removeLabel(target)
  }

  updateConnection(connection: BpmnElement): void {
    this.connections.update(connection)
    this.diSync.updateParent(connection)
    this.diSync.updateWaypoints(connection)
    const label = connection.label as BpmnElement | undefined
    if (label && label.parent) this.diSync.updateLabel(label)
  }

  updateAttachment(shape: BpmnElement): void {
    const bo = getBusinessObject(shape)
    if (!is(bo, 'bpmn:BoundaryEvent')) return
    bo.attachedToRef = shape.host ? getBusinessObject(shape.host as BpmnElement) : undefined
  }

  private definitions(): ModdleElement | undefined {
    const root = this.canvas.getRootElements()[0] as BpmnElement | undefined
    return root ? getDefinitions(getBusinessObject(root)) : undefined
  }
}
