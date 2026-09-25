/**
 * Gemeinsamer Zeichenkontext der Formen-Renderer.
 */

import type { MarkerFactory } from '../markers'
import type { BpmnElement } from '../../types'

export interface DrawContext {
  element: BpmnElement
  fill: string
  stroke: string
  labelColor: string
  markers: MarkerFactory
}

export type ShapeDrawer = (parent: SVGElement, context: DrawContext) => SVGElement

/** Maße einer Form (Diagrammelemente sind in diesen Renderern stets Formen). */
export function size(context: DrawContext): { width: number; height: number } {
  const element = context.element as unknown as { width: number; height: number }
  return { width: element.width, height: element.height }
}
