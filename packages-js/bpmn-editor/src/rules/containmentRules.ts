/**
 * Regeln zum Anlegen, Verschieben und Anheften (Container nach BPMN 2.0):
 * Flussknoten gehören in Prozesse, Pools und aufgeklappte Teilprozesse;
 * Randereignisse haften an Aktivitäten; Pools liegen auf der Wurzel.
 */

import type { Element } from 'diagram-js/lib/model/Types'

import { is, isAny, isEventSubProcess, isExpanded, isLabel, isRoot } from '../util/ModelUtil'
import { isParentOf } from './connectRules'
import type { Point } from '../types'

const BORDER_TOLERANCE = 15

/** Nimmt das Ziel Flussknoten auf? */
export function canDropFlowNode(target: Element): boolean {
  if (is(target, 'bpmn:Participant')) return isExpanded(target)
  if (is(target, 'bpmn:Lane')) return true
  if (is(target, 'bpmn:SubProcess')) return !target.parent || isExpanded(target)
  return !target.parent && is(target, 'bpmn:Process')
}

function canDropArtifact(target: Element): boolean {
  if (!target.parent) return true
  if (isAny(target, ['bpmn:Participant', 'bpmn:Lane'])) return true
  return is(target, 'bpmn:SubProcess') && isExpanded(target)
}

function canDropDataIo(target: Element): boolean {
  if (!target.parent) return is(target, 'bpmn:Process')
  return isAny(target, ['bpmn:Participant', 'bpmn:Lane'])
}

function canDropFlowElement(element: Element, target: Element): boolean {
  if (is(element, 'bpmn:StartEvent') && isEventSubProcess(target)) return true
  return canDropFlowNode(target) && element !== target && !isParentOf(element, target)
}

type DropRule = [string[], (element: Element, target: Element) => boolean]

/** Ablageregeln je Elementart (erste passende gewinnt). */
const DROP_RULES: DropRule[] = [
  [['bpmn:Lane'], (_element, target) => isAny(target, ['bpmn:Participant', 'bpmn:Lane'])],
  [['bpmn:Participant'], (_element, target) => !target.parent && isAny(target, ['bpmn:Process', 'bpmn:Collaboration'])],
  [['bpmn:BoundaryEvent'], () => false],
  [['bpmn:TextAnnotation', 'bpmn:Group'], (_element, target) => canDropArtifact(target)],
  [['bpmn:DataInput', 'bpmn:DataOutput'], (_element, target) => canDropDataIo(target)],
  [['bpmn:FlowElement'], canDropFlowElement],
]

export function canDrop(element: Element, target: Element): boolean {
  if (isLabel(element)) return true
  const rule = DROP_RULES.find(([types]) => isAny(element, types))
  return rule ? rule[1](element, target) : false
}

export function canCreate(shape: Element, target: Element | undefined, source?: Element): boolean {
  if (!target) return false
  if (isLabel(shape)) return true
  if (isLabel(target) || target.waypoints) return false
  if (source && isParentOf(shape, source)) return false
  return canDrop(shape, target)
}

export function canMove(elements: Element[], target: Element | undefined): boolean {
  if (elements.some((element) => isRoot(element))) return false
  // Bahnen werden nur mit ihrem Pool verschoben.
  if (elements.some((element) => is(element, 'bpmn:Lane') && !elements.includes(element.parent as Element))) return false
  if (!target) return true
  // Mitgeführte Elemente (Kinder, Beschriftungen, Randereignisse) folgen ihrem Träger.
  const carried = (element: Element) => isLabel(element) || elements.includes(element.host) || elements.includes(element.parent as Element)
  return elements.every((element) => carried(element) || canDrop(element, target))
}

/** Ein vom Wirt gelöstes Randereignis darf als Zwischenereignis abgelegt werden. */
export function canReplaceOnMove(elements: Element[], target: Element | undefined): boolean {
  const [element] = elements
  if (!target || !element || elements.length !== 1) return false
  if (!is(element, 'bpmn:BoundaryEvent') || elements.includes(element.host)) return false
  return !isLabel(target) && canDropFlowNode(target)
}

/** Liegt der Punkt auf (bzw. nahe) der Außenkante des Ziels? */
export function isPointOnBorder(target: Element, point: Point, tolerance = BORDER_TOLERANCE): boolean {
  const { x, y, width, height } = target as unknown as { x: number; y: number; width: number; height: number }
  const inOuter = point.x >= x - tolerance && point.x <= x + width + tolerance && point.y >= y - tolerance && point.y <= y + height + tolerance
  const inInner = point.x > x + tolerance && point.x < x + width - tolerance && point.y > y + tolerance && point.y < y + height - tolerance
  return inOuter && !inInner
}

function isAttachableEvent(element: Element): boolean {
  return is(element, 'bpmn:Event') && !isAny(element, ['bpmn:StartEvent', 'bpmn:EndEvent']) && (element.incoming || []).length === 0
}

export function canAttach(elements: Element | Element[], target: Element | undefined, position?: Point): false | 'attach' {
  const list = Array.isArray(elements) ? elements : [elements]
  const [element] = list
  if (list.length !== 1 || !element || !target || isLabel(element) || isLabel(target)) return false
  if (!isAttachableEvent(element)) return false
  if (!is(target, 'bpmn:Activity') || isEventSubProcess(target)) return false
  if (position && !isPointOnBorder(target, position)) return false
  return 'attach'
}
