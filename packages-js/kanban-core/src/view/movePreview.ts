/** Vorschau einer laufenden Verschiebung (Tastatur und Zeiger) als reine Funktionen. */
import type { Placement } from '../commands'
import type { Card } from '../model'
import type { ColumnView } from './board'

export interface MovePreview {
  cardId: string
  columnId: string
  /** Position unter den sichtbaren Karten der Zielspalte, ohne die bewegte Karte. */
  index: number
}

/** Spaltenansicht mit der bewegten Karte an der Vorschauposition. */
export function applyPreview(columns: readonly ColumnView[], preview: MovePreview | null): ColumnView[] {
  if (!preview) return [...columns]
  const moving = columns.flatMap((view) => view.cards).find((card) => card.id === preview.cardId)
  if (!moving) return [...columns]
  return columns.map((view) => {
    const cards = view.cards.filter((card) => card.id !== preview.cardId)
    if (view.column.id === preview.columnId) cards.splice(Math.max(0, Math.min(preview.index, cards.length)), 0, moving)
    return { ...view, cards }
  })
}

/**
 * Platzierung für den Port aus der sichtbaren Nachbarschaft: vor der Karte an
 * `index`, sonst hinter der letzten sichtbaren Karte, sonst ans Ende. So bleibt
 * die Position auch bei aktivem Filter eindeutig.
 */
export function placementFor(visible: readonly Card[], index: number): Placement {
  const next = visible[index]
  if (next) return { before_id: next.id }
  const last = visible[visible.length - 1]
  return last ? { after_id: last.id } : {}
}

/** Sichtbare Karten einer Spalte ohne die bewegte Karte. */
export function siblingsOf(columns: readonly ColumnView[], columnId: string, cardId: string): Card[] {
  return columns.find((view) => view.column.id === columnId)?.cards.filter((card) => card.id !== cardId) ?? []
}

/** Aktuelle Spalte und Position einer Karte in der Ansicht. */
export function locate(columns: readonly ColumnView[], cardId: string): { columnId: string; index: number } | null {
  for (const view of columns) {
    const index = view.cards.findIndex((card) => card.id === cardId)
    if (index >= 0) return { columnId: view.column.id, index }
  }
  return null
}

/** Nächste Spalte in Richtung `step` (±1), in die `allowed` die Karte lässt. */
export function neighbourColumn(columns: readonly ColumnView[], from: string, step: -1 | 1, allowed: (columnId: string) => boolean): string | null {
  const start = columns.findIndex((view) => view.column.id === from)
  for (let position = start + step; position >= 0 && position < columns.length; position += step) {
    const candidate = columns[position]?.column.id
    if (candidate && allowed(candidate)) return candidate
  }
  return null
}

type Step = -1 | 0 | 1

/** Nächste Vorschau bei einer Pfeiltaste im Aufnahmemodus; null, wenn kein Ziel erlaubt ist. */
export function stepPreview(columns: readonly ColumnView[], current: MovePreview, dx: Step, dy: Step, allowed: (columnId: string) => boolean): MovePreview | null {
  if (dx !== 0) {
    const target = neighbourColumn(columns, current.columnId, dx, allowed)
    if (!target) return null
    return { ...current, columnId: target, index: Math.min(current.index, siblingsOf(columns, target, current.cardId).length) }
  }
  const size = siblingsOf(columns, current.columnId, current.cardId).length
  return { ...current, index: Math.max(0, Math.min(size, current.index + dy)) }
}

/** Ziel für Strg+Pfeil (cockpit): eine Position bzw. die nächste erlaubte Spalte bei gleicher Position. */
export function nudgeTarget(columns: readonly ColumnView[], cardId: string, dx: Step, dy: Step, allowed: (columnId: string) => boolean): MovePreview | null {
  const place = locate(columns, cardId)
  if (!place) return null
  let target: MovePreview = { cardId, ...place, index: place.index + dy }
  if (dx !== 0) {
    const columnId = neighbourColumn(columns, place.columnId, dx, allowed)
    if (!columnId) return null
    target = { cardId, columnId, index: Math.min(place.index, siblingsOf(columns, columnId, cardId).length) }
  }
  const size = siblingsOf(columns, target.columnId, cardId).length
  return target.index < 0 || target.index > size ? null : target
}
