/**
 * Externe Beschriftungen:
 * - Beim Anlegen eines benannten Elements (z. B. beim Einfügen) entsteht
 *   die Beschriftung mit.
 * - Namensänderungen über `updateProperties` legen Beschriftungen an,
 *   passen sie an oder entfernen sie.
 * - Beschriftungen von Kanten folgen dem Kantenverlauf.
 */

import CommandInterceptor from 'diagram-js/lib/command/CommandInterceptor'

import { getPathMid } from '../../util/LabelUtil'
import { getBusinessObject, is } from '../../util/ModelUtil'
import type { BpmnElement, CommandEvent, EventBus, ModdleElement, Point } from '../../types'
import { syncExternalLabel } from '../cmd/UpdateLabelHandler'
import type Modeling from '../Modeling'

interface CreateContext {
  shape?: BpmnElement
  connection?: BpmnElement
  elements?: BpmnElement[]
  hints?: { skipLabelCreation?: boolean }
}

interface PropertiesContext {
  element: BpmnElement
  moddleElement?: ModdleElement
  properties?: Record<string, unknown>
}

interface WaypointsContext {
  connection?: BpmnElement
  oldWaypoints?: Point[]
  hints?: { labelBehavior?: boolean }
}

const LABEL_PROPERTIES = ['name', 'text', 'value', 'categoryValueRef']

export default class LabelBehavior extends CommandInterceptor {
  static $inject = ['eventBus', 'modeling']

  constructor(
    eventBus: EventBus,
    private readonly modeling: Modeling,
  ) {
    super(eventBus)

    // Beim Einfügen mehrerer Elemente kommen Beschriftungen ggf. mit; erst danach ergänzen.
    this.preExecute('elements.create', 2000, (event: CommandEvent<CreateContext>) => {
      event.context.hints = { ...(event.context.hints || {}), skipLabelCreation: true }
    })
    this.postExecute('elements.create', (event: CommandEvent<CreateContext>) => {
      for (const element of event.context.elements || []) this.ensureLabel(element)
    })
    this.postExecute(['shape.create', 'connection.create'], (event: CommandEvent<CreateContext>) => {
      const { context } = event
      if (!context.hints?.skipLabelCreation) this.ensureLabel(context.shape || context.connection)
    })
    this.postExecute(['element.updateProperties', 'element.updateModdleProperties'], (event: CommandEvent<PropertiesContext>) =>
      this.onPropertiesChanged(event.context),
    )
    this.postExecute(['connection.layout', 'connection.updateWaypoints', 'connection.reconnect'], (event: CommandEvent<WaypointsContext>) =>
      this.followConnection(event.context),
    )
  }

  private ensureLabel(element: BpmnElement | undefined): void {
    if (element && !element.labelTarget) syncExternalLabel(this.modeling, element)
  }

  private onPropertiesChanged(context: PropertiesContext): void {
    const element = context.element
    const bo = getBusinessObject(element)
    const keys = Object.keys(context.properties || {})
    const groupValue = !!context.moddleElement && context.moddleElement !== bo && is(bo, 'bpmn:Group')
    if (!groupValue && !keys.some((key) => LABEL_PROPERTIES.includes(key))) return
    this.ensureLabel((element.labelTarget as BpmnElement | undefined) || element)
  }

  /** Kantenbeschriftung wandert mit dem Mittelpunkt der Kante. */
  private followConnection(context: WaypointsContext): void {
    const connection = context.connection
    const label = connection?.label as BpmnElement | undefined
    if (!connection || !label || context.hints?.labelBehavior === false) return
    if (!context.oldWaypoints?.length) return
    const before = getPathMid(context.oldWaypoints)
    const after = getPathMid(connection.waypoints as Point[])
    const delta = { x: Math.round(after.x - before.x), y: Math.round(after.y - before.y) }
    if (delta.x || delta.y) this.modeling.moveShape(label as never, delta)
  }
}
