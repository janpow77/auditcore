/**
 * Modellierungsregeln nach BPMN 2.0 – Anbindung an den diagram-js-
 * Regeldienst. Die fachlichen Regeln stehen in `connectRules`,
 * `containmentRules` und `resizeRules`.
 */

import RuleProvider from 'diagram-js/lib/features/rules/RuleProvider'
import type { Element } from 'diagram-js/lib/model/Types'

import { is, isExpanded, isLabel } from '../util/ModelUtil'
import type { Bounds, EventBus, Point } from '../types'
import { canConnect, canStartConnection, type ConnectResult } from './connectRules'
import { canAttach, canCreate, canMove, canReplaceOnMove } from './containmentRules'
import { canResize } from './resizeRules'

interface RuleContext {
  source?: Element
  target?: Element
  connection?: Element
  shape?: Element
  shapes?: Element[]
  elements?: Element[]
  element?: Element
  position?: Point
  newBounds?: Bounds
  hints?: { targetParent?: Element; targetAttach?: boolean }
}

function arrangeable(element: Element): boolean {
  return !isLabel(element) && !element.waypoints && !is(element, 'bpmn:Lane') && !is(element, 'bpmn:BoundaryEvent')
}

export default class BpmnRules extends RuleProvider {
  static $inject = ['eventBus']

  constructor(eventBus: EventBus) {
    super(eventBus)
  }

  init(): void {
    const rules: [string, (context: RuleContext) => unknown][] = [
      ['connection.start', (context) => canStartConnection(context.source)],
      ['connection.create', (context) => this.canCreateConnection(context)],
      ['connection.reconnect', (context) => canConnect(context.source, context.target, context.connection)],
      ['connection.updateWaypoints', (context) => ({ type: context.connection?.type })],
      ['shape.resize', (context) => !!context.shape && canResize(context.shape, context.newBounds)],
      ['elements.create', (context) => this.canCreateElements(context)],
      ['elements.move', (context) => this.canMoveElements(context)],
      ['shape.create', (context) => !!context.shape && canCreate(context.shape, context.target, context.source)],
      ['shape.attach', (context) => !!context.shape && canAttach(context.shape, context.target, context.position)],
      ['element.copy', (context) => this.canCopy(context.elements || [], context.element)],
      ['element.autoResize', (context) => this.canAutoResize(context)],
      ['elements.align', (context) => (context.elements || []).filter(arrangeable)],
      ['elements.distribute', (context) => (context.elements || []).filter(arrangeable)],
      ['elements.delete', (context) => (context.elements || []).filter((element) => !!element.parent || isLabel(element))],
    ]
    for (const [action, rule] of rules) this.addRule(action, rule as never)
  }

  /** Öffentliche Prüfung für Modellierung und Oberfläche. */
  canConnect(source: Element | undefined, target: Element | undefined, connection?: Element | null): ConnectResult {
    return canConnect(source, target, connection)
  }

  canAttach(elements: Element | Element[], target: Element | undefined, _source?: unknown, position?: Point): false | 'attach' {
    return canAttach(elements, target, position)
  }

  canCreate(shape: Element, target: Element | undefined, source?: Element): boolean {
    return canCreate(shape, target, source)
  }

  canMove(elements: Element[], target: Element | undefined): boolean {
    return canMove(elements, target)
  }

  canResize(shape: Element, newBounds?: Bounds): boolean {
    return canResize(shape, newBounds)
  }

  /** Beim Anhängen neuer Formen gilt der vorgesehene Elternteil schon beim Prüfen. */
  private canCreateConnection(context: RuleContext): ConnectResult {
    const { source, target, hints } = context
    if (hints?.targetAttach) return false
    if (!target || !hints?.targetParent) return canConnect(source, target)
    const previous = target.parent
    target.parent = hints.targetParent
    try {
      return canConnect(source, target)
    } finally {
      target.parent = previous
    }
  }

  private canCreateElements(context: RuleContext): boolean {
    return (context.elements || []).every((element) => {
      if (element.waypoints) return true
      if (element.host) return !!canAttach(element, element.host, context.position)
      return canCreate(element, context.target)
    })
  }

  private canMoveElements(context: RuleContext): unknown {
    const shapes = context.shapes || []
    return canAttach(shapes, context.target, context.position) || canReplaceOnMove(shapes, context.target) || canMove(shapes, context.target)
  }

  private canCopy(elements: Element[], element: Element | undefined): boolean {
    if (!element || isLabel(element)) return true
    return !is(element, 'bpmn:Lane') || elements.includes(element.parent as Element)
  }

  /** Bahnen füllen ihren Pool stets aus; sie lösen kein Vergrößern aus. */
  private canAutoResize(context: RuleContext): boolean {
    const target = context.target
    if ((context.elements || []).some((element) => is(element, 'bpmn:Lane'))) return false
    return is(target, 'bpmn:Participant') || (is(target, 'bpmn:SubProcess') && isExpanded(target))
  }
}
