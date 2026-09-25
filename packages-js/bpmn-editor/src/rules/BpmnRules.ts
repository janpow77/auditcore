/**
 * Modellierungsregeln nach BPMN 2.0.
 *
 * Grundlage: OMG BPMN 2.0.2, Kapitel 7.5 (Verbindungsregeln für Sequenz-
 * und Nachrichtenflüsse), 10.2 (Aktivitäten), 10.5 (Ereignisse, insbesondere
 * Randereignisse), 10.6 (Gateways) und 10.4 (Daten).
 */

import RuleProvider from 'diagram-js/lib/features/rules/RuleProvider'

import {
  getBusinessObject,
  hasEventDefinition,
  is,
  isAny,
  isEventSubProcess,
  isExpanded,
  isLabel,
  isRoot,
  type DiagramElement,
} from '../util/ModelUtil'

/* eslint-disable @typescript-eslint/no-explicit-any */

export default class BpmnRules extends (RuleProvider as any) {
  static $inject = ['eventBus']

  constructor(eventBus: any) {
    super(eventBus)
  }

  init(): void {
    this.addRule('connection.start', (context: any) => canStartConnection(context.source))

    this.addRule('connection.create', (context: any) => {
      const { source, target } = context
      const hints = context.hints || {}
      const targetParent = hints.targetParent
      const targetAttach = hints.targetAttach
      // Beim Anhängen neuer Formen: vorläufige Lage berücksichtigen.
      if (targetAttach) return false
      if (targetParent) {
        target.parent = targetParent
      }
      try {
        return this.canConnect(source, target)
      } finally {
        if (targetParent) target.parent = null
      }
    })

    this.addRule('connection.reconnect', (context: any) => {
      return this.canConnect(context.source, context.target, context.connection)
    })

    this.addRule('connection.updateWaypoints', (context: any) => ({ type: context.connection.type }))

    this.addRule('shape.resize', (context: any) => this.canResize(context.shape, context.newBounds))

    this.addRule('elements.create', (context: any) => {
      const { elements, position, target } = context
      return elements.every((element: any) => {
        if (isConnection(element)) return true
        if (element.host) return this.canAttach(element, element.host, null, position)
        return this.canCreate(element, target, null, position)
      })
    })

    this.addRule('elements.move', (context: any) => {
      const { target, shapes, position } = context
      return this.canAttach(shapes, target, null, position) || this.canReplaceOnMove(shapes, target) || this.canMove(shapes, target, position)
    })

    this.addRule('shape.create', (context: any) => {
      return this.canCreate(context.shape, context.target, context.source, context.position)
    })

    this.addRule('shape.attach', (context: any) => {
      return this.canAttach(context.shape, context.target, null, context.position)
    })

    this.addRule('element.copy', (context: any) => this.canCopy(context.elements, context.element))

    this.addRule('element.autoResize', (context: any) => {
      const target = context.target
      const elements: DiagramElement[] = context.elements || []
      // Bahnen füllen ihren Pool stets aus; sie lösen kein Vergrößern aus.
      if (elements.some((element) => is(element, 'bpmn:Lane'))) return false
      return is(target, 'bpmn:Participant') || (is(target, 'bpmn:SubProcess') && isExpanded(target))
    })

    this.addRule('elements.align', (context: any) =>
      context.elements.filter(
        (element: any) => !isLabel(element) && !isConnection(element) && !is(element, 'bpmn:Lane') && !is(element, 'bpmn:BoundaryEvent'),
      ),
    )

    this.addRule('elements.distribute', (context: any) =>
      context.elements.filter(
        (element: any) => !isLabel(element) && !isConnection(element) && !is(element, 'bpmn:Lane') && !is(element, 'bpmn:BoundaryEvent'),
      ),
    )

    this.addRule('elements.delete', (context: any) =>
      context.elements.filter((element: any) => !!element.parent || isLabel(element)),
    )
  }

  // -------------------------------------------------------------------------
  // Verbinden
  // -------------------------------------------------------------------------

  canConnect(source: DiagramElement, target: DiagramElement, connection?: DiagramElement): any {
    if (!source || !target || isLabel(source) || isLabel(target)) return null
    if (isRoot(source) || isRoot(target)) return false
    if (isConnection(source) || isConnection(target)) return false

    if (connection) {
      if (isAny(connection, ['bpmn:DataInputAssociation', 'bpmn:DataOutputAssociation'])) {
        return this.canConnectDataAssociation(source, target)
      }
      if (is(connection, 'bpmn:Association')) {
        return this.canConnectAssociation(source, target) ? { type: 'bpmn:Association' } : false
      }
      if (is(connection, 'bpmn:MessageFlow')) {
        return this.canConnectMessageFlow(source, target) ? { type: 'bpmn:MessageFlow' } : false
      }
      if (is(connection, 'bpmn:SequenceFlow')) {
        return this.canConnectSequenceFlow(source, target) ? { type: 'bpmn:SequenceFlow' } : false
      }
    }

    if (this.canConnectMessageFlow(source, target)) return { type: 'bpmn:MessageFlow' }
    if (this.canConnectSequenceFlow(source, target)) return { type: 'bpmn:SequenceFlow' }

    const dataAssociation = this.canConnectDataAssociation(source, target)
    if (dataAssociation) return dataAssociation

    if (isCompensationBoundary(source) && isForCompensation(target)) {
      return { type: 'bpmn:Association', associationDirection: 'One' }
    }
    if (this.canConnectAssociation(source, target)) {
      return { type: 'bpmn:Association', associationDirection: 'None' }
    }
    return false
  }

  canConnectAssociation(source: DiagramElement, target: DiagramElement): boolean {
    if (source === target) return false
    if (isAny(source, ['bpmn:Group']) || isAny(target, ['bpmn:Group'])) return false
    if (is(source, 'bpmn:TextAnnotation') || is(target, 'bpmn:TextAnnotation')) {
      if (is(source, 'bpmn:TextAnnotation') && is(target, 'bpmn:TextAnnotation')) return false
      return !isParentOf(source, target) && !isParentOf(target, source)
    }
    return isCompensationBoundary(source) && isForCompensation(target)
  }

  canConnectMessageFlow(source: DiagramElement, target: DiagramElement): boolean {
    if (source === target) return false
    const sourceParticipant = getOwnParticipant(source)
    const targetParticipant = getOwnParticipant(target)
    if (!sourceParticipant || !targetParticipant) return false
    if (sourceParticipant === targetParticipant) return false
    return isMessageFlowSource(source) && isMessageFlowTarget(target)
  }

  canConnectSequenceFlow(source: DiagramElement, target: DiagramElement): boolean {
    if (source === target) return false
    if (!isSequenceFlowSource(source) || !isSequenceFlowTarget(target)) return false
    if (getScope(source) !== getScope(target)) return false
    if (is(source, 'bpmn:EventBasedGateway')) {
      const ok =
        is(target, 'bpmn:ReceiveTask') ||
        (is(target, 'bpmn:IntermediateCatchEvent') &&
          (hasEventDefinition(target, 'bpmn:MessageEventDefinition') ||
            hasEventDefinition(target, 'bpmn:TimerEventDefinition') ||
            hasEventDefinition(target, 'bpmn:ConditionalEventDefinition') ||
            hasEventDefinition(target, 'bpmn:SignalEventDefinition')))
      if (!ok) return false
    }
    return true
  }

  canConnectDataAssociation(source: DiagramElement, target: DiagramElement): any {
    const isData = (element: any) =>
      isAny(element, ['bpmn:DataObjectReference', 'bpmn:DataStoreReference', 'bpmn:DataInput', 'bpmn:DataOutput'])
    if (isData(source) && (is(target, 'bpmn:Activity') || is(target, 'bpmn:ThrowEvent'))) {
      if (is(source, 'bpmn:DataOutput')) return false
      return { type: 'bpmn:DataInputAssociation' }
    }
    if (isData(target) && (is(source, 'bpmn:Activity') || is(source, 'bpmn:CatchEvent'))) {
      if (is(target, 'bpmn:DataInput')) return false
      return { type: 'bpmn:DataOutputAssociation' }
    }
    return false
  }

  // -------------------------------------------------------------------------
  // Anlegen, Verschieben, Anheften
  // -------------------------------------------------------------------------

  canCreate(shape: DiagramElement, target: DiagramElement, source?: DiagramElement, position?: any): boolean {
    if (!target) return false
    if (isLabel(shape)) return true
    if (isLabel(target) || isConnection(target)) return false
    if (source && isParentOf(shape, source)) return false
    return canDrop(shape, target, position)
  }

  canMove(elements: DiagramElement[], target: DiagramElement, position?: any): boolean {
    if (elements.some((element: any) => isRoot(element))) return false
    // Bahnen werden nur mit ihrem Pool verschoben.
    if (elements.some((element: any) => is(element, 'bpmn:Lane') && !elements.includes(element.parent))) return false
    if (!target) return true
    return elements.every((element: any) => {
      if (isLabel(element)) return true
      if (element.host && elements.includes(element.host)) return true
      return canDrop(element, target, position)
    })
  }

  /** Ein vom Wirt gelöstes Randereignis darf als Zwischenereignis abgelegt werden. */
  canReplaceOnMove(elements: DiagramElement[], target: DiagramElement): boolean {
    if (!target || elements.length !== 1) return false
    const element = elements[0]
    if (!is(element, 'bpmn:BoundaryEvent') || elements.includes(element.host)) return false
    if (isLabel(target)) return false
    return canDropFlowNode(target)
  }

  canAttach(elements: DiagramElement | DiagramElement[], target: DiagramElement, _source: unknown, position?: any): any {
    const list = Array.isArray(elements) ? elements : [elements]
    if (list.length !== 1) return false
    const element = list[0]
    if (!target || isLabel(element) || isLabel(target)) return false
    if (!is(element, 'bpmn:Event') || isAny(element, ['bpmn:StartEvent', 'bpmn:EndEvent'])) return false
    if (!is(target, 'bpmn:Activity') || isEventSubProcess(target)) return false
    if ((element.incoming || []).length > 0) return false
    if (position && !isPointOnBorder(target, position)) return false
    return 'attach'
  }

  canResize(shape: DiagramElement, newBounds?: any): boolean {
    if (is(shape, 'bpmn:SubProcess')) {
      if (!isExpanded(shape)) return !newBounds || (newBounds.width >= 60 && newBounds.height >= 50)
      return !newBounds || (newBounds.width >= 100 && newBounds.height >= 80)
    }
    if (is(shape, 'bpmn:Lane')) {
      return !newBounds || (newBounds.width >= 60 && newBounds.height >= 60)
    }
    if (is(shape, 'bpmn:Participant')) {
      return !newBounds || (newBounds.width >= 250 && newBounds.height >= 50)
    }
    if (is(shape, 'bpmn:TextAnnotation')) {
      return !newBounds || (newBounds.width >= 50 && newBounds.height >= 30)
    }
    if (is(shape, 'bpmn:Group')) {
      return !newBounds || (newBounds.width >= 60 && newBounds.height >= 60)
    }
    if (isAny(shape, ['bpmn:Task', 'bpmn:CallActivity'])) {
      return !newBounds || (newBounds.width >= 60 && newBounds.height >= 50)
    }
    return false
  }

  canCopy(elements: DiagramElement[], element: DiagramElement): boolean {
    if (isLabel(element)) return true
    if (is(element, 'bpmn:Lane') && !elements.includes(element.parent)) return false
    return true
  }
}

// ---------------------------------------------------------------------------
// Hilfsfunktionen
// ---------------------------------------------------------------------------

function isConnection(element: any): boolean {
  return !!element && !!element.waypoints
}


function isParentOf(possibleParent: any, element: any): boolean {
  let current = element && element.parent
  while (current) {
    if (current === possibleParent) return true
    current = current.parent
  }
  return false
}

function canStartConnection(element: any): boolean {
  if (!element || isLabel(element) || isRoot(element) || isConnection(element)) return false
  return isAny(element, [
    'bpmn:FlowNode',
    'bpmn:InteractionNode',
    'bpmn:DataObjectReference',
    'bpmn:DataStoreReference',
    'bpmn:DataInput',
    'bpmn:DataOutput',
    'bpmn:TextAnnotation',
    'bpmn:Participant',
  ])
}

/** Sichtbarer Gültigkeitsbereich eines Flussknotens (Pool, Teilprozess, Wurzel). */
export function getScope(element: any): any {
  let current = element.host ? element.host.parent : element.parent
  while (current && is(current, 'bpmn:Lane')) current = current.parent
  return current
}

/** Pool, in dem das Element liegt (oder der Pool selbst). */
export function getOwnParticipant(element: any): any {
  let current = element
  while (current) {
    if (is(current, 'bpmn:Participant')) return current
    current = current.parent
  }
  return null
}

function isForCompensation(element: any): boolean {
  return !!getBusinessObject(element)?.isForCompensation
}

function isCompensationBoundary(element: any): boolean {
  return is(element, 'bpmn:BoundaryEvent') && hasEventDefinition(element, 'bpmn:CompensateEventDefinition')
}

function isSequenceFlowSource(element: any): boolean {
  if (!is(element, 'bpmn:FlowNode')) return false
  if (is(element, 'bpmn:EndEvent')) return false
  if (isEventSubProcess(element)) return false
  if (isForCompensation(element)) return false
  if (isCompensationBoundary(element)) return false
  if (is(element, 'bpmn:IntermediateThrowEvent') && hasEventDefinition(element, 'bpmn:LinkEventDefinition')) return false
  return true
}

function isSequenceFlowTarget(element: any): boolean {
  if (!is(element, 'bpmn:FlowNode')) return false
  if (is(element, 'bpmn:StartEvent') || is(element, 'bpmn:BoundaryEvent')) return false
  if (isEventSubProcess(element)) return false
  if (isForCompensation(element)) return false
  if (is(element, 'bpmn:IntermediateCatchEvent') && hasEventDefinition(element, 'bpmn:LinkEventDefinition')) return false
  return true
}

function isMessageFlowSource(element: any): boolean {
  if (is(element, 'bpmn:Participant')) return true
  if (isLabel(element)) return false
  if (is(element, 'bpmn:Activity') && !isEventSubProcess(element)) {
    return !is(element, 'bpmn:ReceiveTask')
  }
  if (isAny(element, ['bpmn:IntermediateThrowEvent', 'bpmn:EndEvent'])) {
    const definitions = getBusinessObject(element).eventDefinitions || []
    return definitions.length === 0 || hasEventDefinition(element, 'bpmn:MessageEventDefinition')
  }
  return false
}

function isMessageFlowTarget(element: any): boolean {
  if (is(element, 'bpmn:Participant')) return true
  if (isLabel(element)) return false
  if (is(element, 'bpmn:Activity') && !isEventSubProcess(element)) {
    return !is(element, 'bpmn:SendTask')
  }
  if (isAny(element, ['bpmn:StartEvent', 'bpmn:IntermediateCatchEvent', 'bpmn:BoundaryEvent'])) {
    const definitions = getBusinessObject(element).eventDefinitions || []
    if (is(element, 'bpmn:StartEvent') && getScope(element) && is(getScope(element), 'bpmn:SubProcess')) return false
    return definitions.length === 0 || hasEventDefinition(element, 'bpmn:MessageEventDefinition')
  }
  return false
}

/** Nimmt das Ziel Flussknoten auf? */
function canDropFlowNode(target: any): boolean {
  if (is(target, 'bpmn:Participant')) return isExpanded(target)
  if (is(target, 'bpmn:Lane')) return true
  if (is(target, 'bpmn:SubProcess')) return isExpanded(target)
  if (!target.parent && is(target, 'bpmn:Process')) return true
  if (!target.parent && is(target, 'bpmn:SubProcess')) return true
  return false
}

function canDrop(element: any, target: any, _position?: any): boolean {
  if (isLabel(element)) return true
  if (is(element, 'bpmn:Lane')) return is(target, 'bpmn:Participant') || is(target, 'bpmn:Lane')
  if (is(element, 'bpmn:Participant')) {
    return !target.parent && (is(target, 'bpmn:Process') || is(target, 'bpmn:Collaboration'))
  }
  if (is(element, 'bpmn:BoundaryEvent')) return false
  if (isAny(element, ['bpmn:TextAnnotation', 'bpmn:Group'])) {
    if (!target.parent) return true
    if (is(target, 'bpmn:Participant') || is(target, 'bpmn:Lane')) return true
    return is(target, 'bpmn:SubProcess') && isExpanded(target)
  }
  if (isAny(element, ['bpmn:DataInput', 'bpmn:DataOutput'])) {
    if (!target.parent) return is(target, 'bpmn:Process')
    return is(target, 'bpmn:Participant') || is(target, 'bpmn:Lane')
  }
  if (is(element, 'bpmn:FlowElement')) {
    if (is(element, 'bpmn:StartEvent') && isEventSubProcess(target)) return true
    if (isEventSubProcess(element) && is(target, 'bpmn:Collaboration')) return false
    return canDropFlowNode(target) && !isParentOf(element, target) && element !== target
  }
  return false
}

/** Liegt der Punkt auf (bzw. nahe) der Außenkante des Ziels? */
function isPointOnBorder(target: any, point: { x: number; y: number }, tolerance = 15): boolean {
  const inside =
    point.x >= target.x - tolerance &&
    point.x <= target.x + target.width + tolerance &&
    point.y >= target.y - tolerance &&
    point.y <= target.y + target.height + tolerance
  if (!inside) return false
  const innerInside =
    point.x > target.x + tolerance &&
    point.x < target.x + target.width - tolerance &&
    point.y > target.y + tolerance &&
    point.y < target.y + target.height - tolerance
  return !innerInside
}

export { canDrop, isPointOnBorder }
