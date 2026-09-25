/**
 * Switching the modelling direction: horizontal or vertical, ported from
 * `flussrichtung.ts` of the audit_designer (`wendeRichtungAn` →
 * `applyDirection`, `haltRichtung` → `keepDirection`).
 *
 * BPMN knows the direction only at pools and lanes (`isHorizontal` of the
 * DI shape). This module rotates existing pools and lanes and keeps newly
 * created pools on the chosen direction.
 */

import type { DiagramElement, ElementRegistry, EventBus, EventCallback, Modeling, ServiceLocator } from '../diagram/services'

export type Direction = 'waagerecht' | 'senkrecht'

const POOL_TYPES = ['bpmn:Participant', 'bpmn:Lane']

function isPool(element: DiagramElement): boolean {
  return POOL_TYPES.includes(element.businessObject?.$type ?? '')
}

/**
 * Rotates one pool or lane: sets the DI flag and swaps width and height –
 * otherwise a vertical pool would stay 600 px wide and 250 px high.
 */
function rotate(element: DiagramElement, horizontal: boolean, modeling: Modeling): void {
  const di = element.di
  if (!di) return
  const current = di.get('isHorizontal')
  const isHorizontalNow = current === undefined ? true : Boolean(current)
  if (isHorizontalNow === horizontal) return
  modeling.updateModdleProperties(element, di, { isHorizontal: horizontal })
  const width = Number(element.width ?? 0)
  const height = Number(element.height ?? 0)
  if (width > 0 && height > 0) {
    modeling.resizeShape(element, { x: Number(element.x ?? 0), y: Number(element.y ?? 0), width: height, height: width })
  }
}

/** Applies a direction to the whole diagram; returns the number of pools and lanes. */
export function applyDirection(editor: ServiceLocator, direction: Direction): number {
  const registry = editor.get<ElementRegistry>('elementRegistry')
  const modeling = editor.get<Modeling>('modeling')
  const pools = registry.filter(isPool)
  for (const pool of pools) rotate(pool, direction === 'waagerecht', modeling)
  return pools.length
}

/** Keeps newly created pools on the chosen direction; returns an unsubscribe function. */
export function keepDirection(editor: ServiceLocator, readDirection: () => Direction): () => void {
  const eventBus = editor.get<EventBus>('eventBus')
  const modeling = editor.get<Modeling>('modeling')
  const listener: EventCallback = (event) => {
    const shape = (event.context as { shape?: DiagramElement } | undefined)?.shape
    if (shape && isPool(shape)) rotate(shape, readDirection() === 'waagerecht', modeling)
  }
  eventBus.on('commandStack.shape.create.postExecuted', 1000, listener)
  return () => eventBus.off('commandStack.shape.create.postExecuted', listener)
}
