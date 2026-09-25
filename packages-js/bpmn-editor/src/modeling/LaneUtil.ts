/**
 * Hilfen für Bahnen (Lanes).
 *
 * Diagrammstruktur: Alle Bahnen eines Pools – gleich welcher Tiefe – sind
 * Kinder des Pools im Diagrammbaum. Die Verschachtelung steht allein im
 * semantischen Modell (`childLaneSet`). Flussknoten sind ebenfalls Kinder
 * des Pools; ihre Bahnzugehörigkeit ergibt sich aus der Lage
 * (`flowNodeRef`).
 */

import { getBusinessObject, is, isHorizontal } from '../util/ModelUtil'
import type { BpmnElement, Bounds, ModdleElement } from '../types'

export const LANE_BAND = 30
export const DEFAULT_LANE_SIZE = 120
export const MIN_LANE_SIZE = 60

export type { Bounds }

type Shape = BpmnElement & Bounds

export function getParticipant(element: BpmnElement | undefined | null): BpmnElement | null {
  let current: BpmnElement | undefined | null = element
  while (current && !is(current, 'bpmn:Participant')) current = current.parent as BpmnElement | undefined
  return current || null
}

function childrenOf(element: BpmnElement | null | undefined): BpmnElement[] {
  return ((element?.children || []) as BpmnElement[]).slice()
}

/** Alle Bahnformen eines Pools (jeder Tiefe). */
export function getAllLanes(participant: BpmnElement | null | undefined): Shape[] {
  return childrenOf(participant).filter((child) => is(child, 'bpmn:Lane') && !child.labelTarget) as Shape[]
}

function semanticChildLanes(container: BpmnElement): ModdleElement[] {
  const bo = getBusinessObject(container)
  if (is(bo, 'bpmn:Participant')) {
    const laneSets = bo.processRef?.laneSets || []
    return laneSets.flatMap((set) => set.lanes || [])
  }
  return bo.childLaneSet?.lanes || []
}

/** Unmittelbare Unterbahnen einer Bahn bzw. die obersten Bahnen eines Pools. */
export function getChildLanes(container: BpmnElement): Shape[] {
  const participant = is(container, 'bpmn:Participant') ? container : getParticipant(container)
  const children = semanticChildLanes(container)
  return getAllLanes(participant).filter((lane) => children.includes(getBusinessObject(lane)))
}

/** Elternform im Sinne der Verschachtelung: übergeordnete Bahn oder Pool. */
export function getLaneParent(lane: BpmnElement): BpmnElement | null {
  const participant = getParticipant(lane)
  const parentLane = getBusinessObject(lane).$parent?.$parent
  if (parentLane && is(parentLane, 'bpmn:Lane')) {
    return getAllLanes(participant).find((other) => getBusinessObject(other) === parentLane) || participant
  }
  return participant
}

/** Alle Unterbahnen (rekursiv). */
export function getDescendantLanes(lane: BpmnElement): Shape[] {
  return getChildLanes(lane).flatMap((child) => [child, ...getDescendantLanes(child)])
}

export interface Axis {
  main: 'x' | 'y'
  mainSize: 'width' | 'height'
  cross: 'x' | 'y'
  crossSize: 'width' | 'height'
}

export function getAxis(element: BpmnElement): Axis {
  return isHorizontal(element)
    ? { main: 'y', mainSize: 'height', cross: 'x', crossSize: 'width' }
    : { main: 'x', mainSize: 'width', cross: 'y', crossSize: 'height' }
}

export function toBounds(element: BpmnElement): Bounds {
  const shape = element as unknown as Bounds
  return { x: shape.x, y: shape.y, width: shape.width, height: shape.height }
}

/** Innenbereich (ohne Kopfband) eines Pools bzw. einer Bahn. */
export function getContentBounds(element: BpmnElement, axis: Axis = getAxis(element)): Bounds {
  const bounds = toBounds(element)
  bounds[axis.cross] += LANE_BAND
  bounds[axis.crossSize] -= LANE_BAND
  return bounds
}

/** Verteilt eine Größenänderung auf Bahnen (von hinten bzw. vorne), ohne Mindestgröße zu unterschreiten. */
function distribute(sizes: number[], total: number, absorbAtStart: boolean): number[] {
  const result = sizes.slice()
  let delta = total - result.reduce((sum, size) => sum + size, 0)
  const order = result.map((_, index) => (absorbAtStart ? index : result.length - 1 - index))
  for (const index of order) {
    if (delta === 0) break
    const current = result[index] ?? 0
    const next = Math.max(MIN_LANE_SIZE, current + delta)
    delta -= next - current
    result[index] = next
  }
  return result
}

/**
 * Ordnet die Bahnen eines Pools innerhalb der gegebenen Grenzen an.
 * `absorbAtStart`: Größenänderung übernimmt die erste statt der letzten Bahn.
 */
export function computeLanesLayout(participant: BpmnElement, participantBounds: Bounds, absorbAtStart = false): Map<BpmnElement, Bounds> {
  const result = new Map<BpmnElement, Bounds>()
  const axis = getAxis(participant)
  const layoutLevel = (container: BpmnElement, containerBounds: Bounds) => {
    const lanes = getChildLanes(container).sort((a, b) => a[axis.main] - b[axis.main])
    if (lanes.length === 0) return
    const content = { ...containerBounds }
    content[axis.cross] += LANE_BAND
    content[axis.crossSize] -= LANE_BAND
    const sizes = distribute(
      lanes.map((lane) => lane[axis.mainSize]),
      content[axis.mainSize],
      absorbAtStart,
    )
    let position = content[axis.main]
    lanes.forEach((lane, index) => {
      const size = sizes[index] ?? 0
      const bounds = { ...content, [axis.main]: position, [axis.mainSize]: size }
      position += size
      result.set(lane, bounds)
      layoutLevel(lane, bounds)
    })
  }
  layoutLevel(participant, participantBounds)
  return result
}

export function boundsEqual(a: Bounds, b: Bounds): boolean {
  return (
    Math.round(a.x) === Math.round(b.x) &&
    Math.round(a.y) === Math.round(b.y) &&
    Math.round(a.width) === Math.round(b.width) &&
    Math.round(a.height) === Math.round(b.height)
  )
}

/**
 * Verschiebt eine Kante (Koordinate `edge` auf Achse `axisKey`) um `delta`:
 * Alle Formen, deren Anfang bzw. Ende auf dieser Kante liegt, wachsen oder
 * schrumpfen entsprechend. Ergebnisse landen in `planned`.
 */
export function moveEdge(shapes: BpmnElement[], axisKey: 'x' | 'y', edge: number, delta: number, planned: Map<BpmnElement, Bounds>): void {
  const sizeKey = axisKey === 'x' ? 'width' : 'height'
  for (const shape of shapes) {
    const bounds = planned.get(shape) || toBounds(shape)
    const start = bounds[axisKey]
    const end = start + bounds[sizeKey]
    if (Math.abs(start - edge) < 1) {
      planned.set(shape, { ...bounds, [axisKey]: start + delta, [sizeKey]: bounds[sizeKey] - delta })
    } else if (Math.abs(end - edge) < 1) {
      planned.set(shape, { ...bounds, [sizeKey]: bounds[sizeKey] + delta })
    }
  }
}
