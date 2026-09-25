/**
 * Hilfen für Bahnen (Lanes).
 *
 * Diagrammstruktur: Alle Bahnen eines Pools – gleich welcher Tiefe – sind
 * Kinder des Pools im Diagrammbaum. Die Verschachtelung steht allein im
 * semantischen Modell (`childLaneSet`). Flussknoten sind ebenfalls Kinder
 * des Pools; ihre Bahnzugehörigkeit ergibt sich aus der Lage
 * (`flowNodeRef`).
 */

import { getBusinessObject, is, isHorizontal, type DiagramElement } from '../util/ModelUtil'

/* eslint-disable @typescript-eslint/no-explicit-any */

export const LANE_BAND = 30
export const DEFAULT_LANE_SIZE = 120
export const MIN_LANE_SIZE = 60

export type Bounds = { x: number; y: number; width: number; height: number }

export function getParticipant(element: DiagramElement): DiagramElement | null {
  let current = element
  while (current && !is(current, 'bpmn:Participant')) current = current.parent
  return current || null
}

/** Alle Bahnformen eines Pools (jeder Tiefe). */
export function getAllLanes(participant: DiagramElement): DiagramElement[] {
  return (participant?.children || []).filter((child: any) => is(child, 'bpmn:Lane') && !child.labelTarget)
}

/** Unmittelbare Unterbahnen einer Bahn bzw. die obersten Bahnen eines Pools. */
export function getChildLanes(container: DiagramElement): DiagramElement[] {
  const participant = is(container, 'bpmn:Participant') ? container : getParticipant(container)
  const lanes = getAllLanes(participant)
  const bo = getBusinessObject(container)
  let semanticChildren: any[] = []
  if (is(bo, 'bpmn:Participant')) {
    const process = bo.processRef
    semanticChildren = process ? (process.laneSets || []).flatMap((set: any) => set.lanes || []) : []
  } else if (bo.childLaneSet) {
    semanticChildren = bo.childLaneSet.lanes || []
  }
  return lanes.filter((lane: any) => semanticChildren.includes(getBusinessObject(lane)))
}

/** Geschwisterbahnen (einschließlich der Bahn selbst). */
export function getSiblingLanes(lane: DiagramElement): DiagramElement[] {
  const participant = getParticipant(lane)
  const laneSet = getBusinessObject(lane).$parent
  return getAllLanes(participant).filter((other: any) => getBusinessObject(other).$parent === laneSet)
}

/** Elternform im Sinne der Verschachtelung: übergeordnete Bahn oder Pool. */
export function getLaneParent(lane: DiagramElement): DiagramElement | null {
  const participant = getParticipant(lane)
  const laneSet = getBusinessObject(lane).$parent
  const parentLaneBo = laneSet && laneSet.$parent
  if (parentLaneBo && is(parentLaneBo, 'bpmn:Lane')) {
    return getAllLanes(participant).find((other: any) => getBusinessObject(other) === parentLaneBo) || participant
  }
  return participant
}

/** Alle Unterbahnen (rekursiv). */
export function getDescendantLanes(lane: DiagramElement): DiagramElement[] {
  const result: DiagramElement[] = []
  const walk = (current: DiagramElement) => {
    for (const child of getChildLanes(current)) {
      result.push(child)
      walk(child)
    }
  }
  walk(lane)
  return result
}

export interface Axis {
  main: 'x' | 'y'
  mainSize: 'width' | 'height'
  cross: 'x' | 'y'
  crossSize: 'width' | 'height'
}

export function getAxis(element: DiagramElement): Axis {
  return isHorizontal(element)
    ? { main: 'y', mainSize: 'height', cross: 'x', crossSize: 'width' }
    : { main: 'x', mainSize: 'width', cross: 'y', crossSize: 'height' }
}

/** Innenbereich (ohne Kopfband) eines Pools bzw. einer Bahn. */
export function getContentBounds(element: DiagramElement): Bounds {
  const axis = getAxis(element)
  const bounds: Bounds = { x: element.x, y: element.y, width: element.width, height: element.height }
  bounds[axis.cross] += LANE_BAND
  bounds[axis.crossSize] -= LANE_BAND
  return bounds
}

/**
 * Ordnet die Bahnen eines Pools innerhalb seiner (neuen) Grenzen an.
 * `absorbAtStart`: Größenänderung wird von der ersten statt der letzten Bahn aufgenommen.
 */
export function computeLanesLayout(
  participant: DiagramElement,
  participantBounds: Bounds,
  absorbAtStart = false,
): Map<DiagramElement, Bounds> {
  const result = new Map<DiagramElement, Bounds>()
  const axis = getAxis(participant)

  const layoutLevel = (container: DiagramElement, containerBounds: Bounds) => {
    const lanes = getChildLanes(container).sort((a: any, b: any) => a[axis.main] - b[axis.main])
    if (lanes.length === 0) return
    const content = { ...containerBounds }
    content[axis.cross] += LANE_BAND
    content[axis.crossSize] -= LANE_BAND

    const sizes = lanes.map((lane: any) => lane[axis.mainSize])
    const total = sizes.reduce((sum: number, size: number) => sum + size, 0)
    let delta = content[axis.mainSize] - total
    const order = absorbAtStart ? sizes.map((_: number, i: number) => i) : sizes.map((_: number, i: number) => sizes.length - 1 - i)
    for (const index of order) {
      if (delta === 0) break
      const next = Math.max(MIN_LANE_SIZE, sizes[index] + delta)
      delta -= next - sizes[index]
      sizes[index] = next
    }

    let position = content[axis.main]
    lanes.forEach((lane: any, index: number) => {
      const bounds: Bounds = { x: 0, y: 0, width: 0, height: 0 }
      bounds[axis.main] = position
      bounds[axis.mainSize] = sizes[index]
      bounds[axis.cross] = content[axis.cross]
      bounds[axis.crossSize] = content[axis.crossSize]
      position += sizes[index]
      result.set(lane, bounds)
      layoutLevel(lane, bounds)
    })
  }

  layoutLevel(participant, participantBounds)
  return result
}

/** Bahn, in deren Innerem der Punkt liegt (tiefste zuerst). */
export function getLanesAt(participant: DiagramElement, point: { x: number; y: number }): DiagramElement[] {
  return getAllLanes(participant).filter(
    (lane: any) =>
      point.x >= lane.x && point.x <= lane.x + lane.width && point.y >= lane.y && point.y <= lane.y + lane.height,
  )
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
 * schrumpfen entsprechend.
 */
export function moveEdge(
  shapes: DiagramElement[],
  axisKey: 'x' | 'y',
  edge: number,
  delta: number,
  current: Map<DiagramElement, Bounds>,
): void {
  const sizeKey = axisKey === 'x' ? 'width' : 'height'
  for (const shape of shapes) {
    const bounds = current.get(shape) || { x: shape.x, y: shape.y, width: shape.width, height: shape.height }
    const start = bounds[axisKey]
    const end = bounds[axisKey] + bounds[sizeKey]
    if (Math.abs(start - edge) < 1) {
      bounds[axisKey] = start + delta
      bounds[sizeKey] = bounds[sizeKey] - delta
      current.set(shape, { ...bounds })
    } else if (Math.abs(end - edge) < 1) {
      bounds[sizeKey] = bounds[sizeKey] + delta
      current.set(shape, { ...bounds })
    }
  }
}
