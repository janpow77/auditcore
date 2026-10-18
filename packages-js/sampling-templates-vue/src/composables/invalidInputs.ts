/**
 * Eingaben, deren Text gerade nicht als Zahl lesbar ist („abc“). Sie zählen in
 * der Rechnung als leer; die Ergebniszeilen melden sie aber als ungültig, nicht
 * als fehlend. Das Eingabefeld trägt sich ein und aus, die Sitzung reicht die
 * Menge an die Anzeige weiter.
 */
import { inject, onBeforeUnmount, reactive, type InjectionKey } from 'vue'

export type InvalidInputs = Set<string>

export const INVALID_INPUTS: InjectionKey<InvalidInputs> = Symbol('fa-st-invalid-inputs')

/** Neue, reaktive Menge für die Sitzung. */
export const createInvalidInputs = (): InvalidInputs => reactive(new Set<string>()) as InvalidInputs

/** Für ein Eingabefeld: meldet, ob seine Zelle gerade ungültig ist; beim Verlassen des Formulars wird sie ausgetragen. */
export function useInvalidMark(cell: () => string): (invalid: boolean) => void {
  const inputs = inject(INVALID_INPUTS, null)
  onBeforeUnmount(() => inputs?.delete(cell()))
  return (invalid) => {
    if (!inputs) return
    if (invalid) inputs.add(cell())
    else inputs.delete(cell())
  }
}
