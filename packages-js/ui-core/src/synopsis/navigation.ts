/** Tastatur- und Fokussteuerung der Synopse (framework-frei). */

const NEXT_KEYS = new Set(['n', 'j'])
const PREV_KEYS = new Set(['p', 'k'])

function isEditable(target: EventTarget | null): boolean {
  if (typeof HTMLElement === 'undefined' || !(target instanceof HTMLElement)) return false
  return target.isContentEditable || ['INPUT', 'TEXTAREA', 'SELECT'].includes(target.tagName)
}

function prefersReducedMotion(): boolean {
  return typeof window.matchMedia === 'function' && window.matchMedia('(prefers-reduced-motion: reduce)').matches
}

/** Richtung für N/J (nächste) bzw. P/K (vorige Änderung); in Eingabefeldern und mit Modifikatoren `null`. */
export function navigationDirection(event: Pick<KeyboardEvent, 'key' | 'altKey' | 'ctrlKey' | 'metaKey' | 'target'>): 1 | -1 | null {
  if (event.altKey || event.ctrlKey || event.metaKey || isEditable(event.target)) return null
  const key = event.key.toLowerCase()
  if (NEXT_KEYS.has(key)) return 1
  return PREV_KEYS.has(key) ? -1 : null
}

/** Zeile fokussieren und sichtbar machen; Zeilen tragen `data-row-id` und `tabindex="-1"`. */
export function focusRow(root: HTMLElement | null, id: string): void {
  const target = Array.from(root?.querySelectorAll<HTMLElement>('[data-row-id]') ?? []).find(
    (element) => element.dataset.rowId === id,
  )
  if (!target) return
  target.focus({ preventScroll: true })
  if (typeof target.scrollIntoView === 'function') {
    target.scrollIntoView({ block: 'center', behavior: prefersReducedMotion() ? 'auto' : 'smooth' })
  }
}
