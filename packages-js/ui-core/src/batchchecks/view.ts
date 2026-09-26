import type { BatchchecksData } from './controller'
import type { BatchchecksItem } from './types'

/** Zeile der Liste, wie Vue und React sie darstellen. */
export interface BatchchecksRow {
  id: string
  label: string
  selected: boolean
}

export function batchchecksRows(state: BatchchecksData): BatchchecksRow[] {
  return state.items.map((item) => ({ id: item.id, label: item.label, selected: item.id === state.selectedId }))
}

export function batchchecksSelection(state: BatchchecksData): BatchchecksItem | null {
  return state.items.find((item) => item.id === state.selectedId) ?? null
}

/** Hinweis „keine Einträge“ nur nach abgeschlossener, fehlerfreier Anfrage. */
export function batchchecksIsEmpty(state: BatchchecksData): boolean {
  return state.busy === null && state.error === null && state.items.length === 0
}
