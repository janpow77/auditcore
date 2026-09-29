import type { AccountData } from './controller'
import type { AccountItem } from './types'

/** Zeile der Liste, wie Vue und React sie darstellen. */
export interface AccountRow {
  id: string
  label: string
  selected: boolean
}

export function accountRows(state: AccountData): AccountRow[] {
  return state.items.map((item) => ({ id: item.id, label: item.label, selected: item.id === state.selectedId }))
}

export function accountSelection(state: AccountData): AccountItem | null {
  return state.items.find((item) => item.id === state.selectedId) ?? null
}

/** Hinweis „keine Einträge“ nur nach abgeschlossener, fehlerfreier Anfrage. */
export function accountIsEmpty(state: AccountData): boolean {
  return state.busy === null && state.error === null && state.items.length === 0
}
