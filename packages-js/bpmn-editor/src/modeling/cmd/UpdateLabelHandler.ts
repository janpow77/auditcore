/**
 * Befehl `element.updateLabel`: setzt den Beschriftungstext und legt externe
 * Beschriftungen bei Bedarf an, passt sie an oder entfernt sie.
 */

import { getExternalLabelMid, getExternalLabelSize, getLabel, isLabelExternal, setLabel } from '../../util/LabelUtil'
import type { BpmnElement, Bounds, Point } from '../../types'
import type Modeling from '../Modeling'

interface UpdateLabelContext {
  element: BpmnElement
  newLabel: string | null | undefined
  newBounds?: Bounds
  labelTarget?: BpmnElement
  oldLabel?: string
}

export function normalizeText(text: unknown): string | undefined {
  if (text === null || text === undefined) return undefined
  const value = String(text)
  return value.trim().length === 0 ? undefined : value
}

/** Lage einer neuen Beschriftung: aus der DI oder Standardlage unter bzw. über dem Element. */
function initialLabelBox(target: BpmnElement, text: string): { center: Point; width: number; height: number } {
  const bounds = target.di?.label?.bounds
  if (bounds) {
    const width = bounds.width ?? 0
    const height = bounds.height ?? 0
    return { center: { x: (bounds.x ?? 0) + width / 2, y: (bounds.y ?? 0) + height / 2 }, width, height }
  }
  const size = getExternalLabelSize(text)
  const mid = getExternalLabelMid(target)
  return { center: { x: mid.x, y: mid.y - 10 + size.height / 2 }, ...size }
}

function createExternalLabel(modeling: Modeling, target: BpmnElement, text: string): void {
  const box = initialLabelBox(target, text)
  modeling.createLabel(target as never, box.center, {
    id: `${target.id}_label`,
    businessObject: target.businessObject,
    di: target.di,
    width: box.width,
    height: box.height,
  } as never)
}

/** Passt die Größe an den Text an; die obere Mitte bleibt stehen. */
function fitExternalLabel(modeling: Modeling, label: BpmnElement & Bounds, text: string): void {
  const size = getExternalLabelSize(text)
  const x = Math.round(label.x + label.width / 2 - size.width / 2)
  if (x === label.x && size.width === label.width && size.height === label.height) return
  modeling.resizeShape(label as never, { x, y: label.y, width: size.width, height: size.height }, { width: 0, height: 0 })
}

/** Stimmt eine externe Beschriftung auf den Text ab (anlegen, anpassen, entfernen). */
export function syncExternalLabel(modeling: Modeling, target: BpmnElement): void {
  if (!target.parent || !isLabelExternal(target)) return
  const text = getLabel(target)
  const label = target.label as (BpmnElement & Bounds) | undefined
  if (text && label) fitExternalLabel(modeling, label, text)
  else if (text) createExternalLabel(modeling, target, text)
  else if (label) modeling.removeShape(label as never)
}

export default class UpdateLabelHandler {
  static $inject = ['modeling']

  constructor(private readonly modeling: Modeling) {}

  execute(context: UpdateLabelContext): BpmnElement[] {
    const target = (context.element.labelTarget as BpmnElement | undefined) || context.element
    context.labelTarget = target
    context.oldLabel = getLabel(target)
    setLabel(target, normalizeText(context.newLabel))
    return target.label ? [target, target.label as BpmnElement] : [target]
  }

  postExecute(context: UpdateLabelContext): void {
    const target = context.labelTarget as BpmnElement
    syncExternalLabel(this.modeling, target)
    if (context.newBounds && !target.waypoints) this.modeling.resizeShape(target as never, context.newBounds)
  }

  revert(context: UpdateLabelContext): BpmnElement[] {
    const target = context.labelTarget as BpmnElement
    setLabel(target, context.oldLabel)
    return target.label ? [target, target.label as BpmnElement] : [target]
  }
}
