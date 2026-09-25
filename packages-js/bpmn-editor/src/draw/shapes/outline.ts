/**
 * Umrisse der Formen als Pfad (für Andockpunkte und Kantenzuschnitt).
 */

import { is, isAny } from '../../util/ModelUtil'
import type { BpmnElement, Point } from '../../types'
import { TASK_BORDER_RADIUS } from './activities'

type Box = { x: number; y: number; width: number; height: number }

function circlePath({ x, y, width }: Box): string {
  const r = width / 2
  const cx = x + r
  const cy = y + r
  return `M ${cx} ${cy - r} A ${r} ${r} 0 1 1 ${cx - 0.01} ${cy - r} Z`
}

function diamondPath({ x, y, width: w, height: h }: Box): string {
  return `M ${x + w / 2} ${y} L ${x + w} ${y + h / 2} L ${x + w / 2} ${y + h} L ${x} ${y + h / 2} Z`
}

function roundedRectPath({ x, y, width: w, height: h }: Box): string {
  const r = TASK_BORDER_RADIUS
  return (
    `M ${x + r} ${y} L ${x + w - r} ${y} A ${r} ${r} 0 0 1 ${x + w} ${y + r} ` +
    `L ${x + w} ${y + h - r} A ${r} ${r} 0 0 1 ${x + w - r} ${y + h} ` +
    `L ${x + r} ${y + h} A ${r} ${r} 0 0 1 ${x} ${y + h - r} ` +
    `L ${x} ${y + r} A ${r} ${r} 0 0 1 ${x + r} ${y} Z`
  )
}

function dataObjectPath({ x, y, width: w, height: h }: Box): string {
  const fold = Math.min(10, w / 3)
  return `M ${x} ${y} L ${x + w - fold} ${y} L ${x + w} ${y + fold} L ${x + w} ${y + h} L ${x} ${y + h} Z`
}

function rectPath({ x, y, width: w, height: h }: Box): string {
  return `M ${x} ${y} L ${x + w} ${y} L ${x + w} ${y + h} L ${x} ${y + h} Z`
}

const OUTLINES: [string[], (box: Box) => string][] = [
  [['bpmn:Event'], circlePath],
  [['bpmn:Gateway'], diamondPath],
  [['bpmn:Activity'], roundedRectPath],
  [['bpmn:DataObjectReference', 'bpmn:DataInput', 'bpmn:DataOutput'], dataObjectPath],
]

export function getShapePath(element: BpmnElement): string {
  const box = element as unknown as Box
  const entry = OUTLINES.find(([types]) => isAny(element, types))
  return entry ? entry[1](box) : rectPath(box)
}

export function getConnectionPath(connection: BpmnElement): string {
  const points = ((connection as unknown as { waypoints?: Point[] }).waypoints || []) as Point[]
  return points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ')
}

export { is }
