import type { RunnerData } from './controller'
import type { RunnerItem } from './types'

/** Zeile der Liste, wie Vue und React sie darstellen. */
export interface RunnerRow {
  id: string
  label: string
  selected: boolean
}

export function runnerRows(state: RunnerData): RunnerRow[] {
  return state.items.map((item) => ({ id: item.id, label: item.label, selected: item.id === state.selectedId }))
}

export function runnerSelection(state: RunnerData): RunnerItem | null {
  return state.items.find((item) => item.id === state.selectedId) ?? null
}

/** Hinweis „keine Einträge“ nur nach abgeschlossener, fehlerfreier Anfrage. */
export function runnerIsEmpty(state: RunnerData): boolean {
  return state.busy === null && state.error === null && state.items.length === 0
}
