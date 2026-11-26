// Vorgaben der Anwendung für Begriffe und Muster (`presetCriteria`): sofort oder vorgemerkt.

import { redactionTerms } from './model'
import type { Resources } from './resources'
import { locked, REVIEW_RESET, type RedactionData, type RedactionPresets, type RedactionStore } from './state'

/** Nur Listen aus Zeichenketten; ein HTML-Attribut (String) zählt nicht als Vorgabe. */
const stringList = (value: unknown): string[] | undefined =>
  Array.isArray(value) ? value.filter((entry): entry is string => typeof entry === 'string') : undefined

/**
 * Vorgaben für Begriffe und Muster. Im Formular gelten sie sofort; ein Plan zu
 * alten Kriterien (vorhanden oder laufend) verfällt dann. Während des Schwärzens
 * und im Ergebnis werden sie vorgemerkt und beim nächsten Schritt übernommen.
 */
export function createPresetQueue(store: RedactionStore, resources: Resources) {
  let pending: RedactionPresets | null = null
  const deferred = (): boolean => locked(store) || store.get().result !== null
  function applyNow(presets: RedactionPresets): void {
    const state = store.get()
    const catalogue = state.catalogue
    const known = catalogue ? new Set(catalogue.patterns.filter((pattern) => pattern.available).map((pattern) => pattern.id)) : null
    const terms = stringList(presets.terms)
    const patterns = stringList(presets.patterns)
    if (!terms && !patterns) return
    const change: Partial<RedactionData> = { validation: null }
    if (terms) change.terms = redactionTerms(terms.join('\n')).join('\n')
    if (patterns) change.patterns = [...new Set(patterns)].filter((id) => !known || known.has(id))
    if (state.plan || state.busy === 'plan') {
      resources.dropAll()
      Object.assign(change, { ...REVIEW_RESET, plan: null, selected: new Set(), criteriaNotice: 'presets' })
    }
    store.set(change)
  }
  return {
    offer(presets: RedactionPresets): void {
      if (deferred()) {
        // Nur gesetzte Schlüssel vormerken, wie im sofortigen Pfad.
        const next: RedactionPresets = { ...pending }
        if (presets.terms !== undefined) next.terms = presets.terms
        if (presets.patterns !== undefined) next.patterns = presets.patterns
        pending = next
      }
      else applyNow(presets)
    },
    /** Vorgemerkte Vorgaben übernehmen, sobald das wieder möglich ist. */
    flush(): void {
      if (!pending || deferred()) return
      const next = pending
      pending = null
      applyNow(next)
    },
  }
}

export type PresetQueue = ReturnType<typeof createPresetQueue>
