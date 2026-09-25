/**
 * Lage eines Menüs unterhalb eines Elements (Bildschirmkoordinaten).
 */

import type { Element } from 'diagram-js/lib/model/Types'

import type { Bounds, Canvas, Point } from '../types'

function boundsOf(elements: Element[]): Bounds {
  const boxes = elements.map((element) => element as unknown as Bounds).filter((box) => typeof box.width === 'number')
  if (boxes.length === 0) return { x: 0, y: 0, width: 0, height: 0 }
  const x = Math.min(...boxes.map((box) => box.x))
  const y = Math.min(...boxes.map((box) => box.y))
  const right = Math.max(...boxes.map((box) => box.x + box.width))
  const bottom = Math.max(...boxes.map((box) => box.y + box.height))
  return { x, y, width: right - x, height: bottom - y }
}

/** Linke untere Ecke des Elements (bzw. der Auswahl) plus Abstand, in Bildschirmkoordinaten. */
export function popupPositionFor(canvas: Canvas, target: Element | Element[], offset = 8): Point {
  const box = boundsOf(Array.isArray(target) ? target : [target])
  const viewbox = canvas.viewbox()
  const rect = canvas.getContainer().getBoundingClientRect()
  return {
    x: Math.round(rect.left + (box.x - viewbox.x) * viewbox.scale),
    y: Math.round(rect.top + (box.y + box.height - viewbox.y) * viewbox.scale + offset),
  }
}
