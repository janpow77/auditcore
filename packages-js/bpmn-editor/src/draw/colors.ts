/**
 * Farbermittlung aus der DI: `color:background-color`/`bioc:fill` für die
 * Füllung, `color:border-color`/`bioc:stroke` für Linien und
 * `color:color` an der Beschriftung.
 */

import { getDi } from '../util/ModelUtil'
import type { BpmnElement, ModdleElement } from '../types'

export interface ColorDefaults {
  fill: string
  stroke: string
  label: string
}

function read(target: ModdleElement | undefined, name: string): string | undefined {
  if (!target) return undefined
  const value = target.get(name)
  return typeof value === 'string' && value ? value : undefined
}

export function getFillColor(element: BpmnElement, fallback: string): string {
  const di = getDi(element) as ModdleElement | undefined
  return read(di, 'color:background-color') || read(di, 'bioc:fill') || fallback
}

export function hasCustomFill(element: BpmnElement): boolean {
  const di = getDi(element) as ModdleElement | undefined
  return !!(read(di, 'color:background-color') || read(di, 'bioc:fill'))
}

export function getStrokeColor(element: BpmnElement, fallback: string): string {
  const di = getDi(element) as ModdleElement | undefined
  return read(di, 'color:border-color') || read(di, 'bioc:stroke') || fallback
}

export function getLabelColor(element: BpmnElement, defaults: ColorDefaults): string {
  const di = getDi(element) as ModdleElement | undefined
  return read(di?.label, 'color:color') || getStrokeColor(element, defaults.label)
}
