/** Fokusfalle für Dialoge, framework-frei (Vue `useFocusTrap`, React `useFocusTrap`). */
const FOCUSABLE = [
  'a[href]',
  'button:not([disabled])',
  'input:not([disabled]):not([type="hidden"])',
  'select:not([disabled])',
  'textarea:not([disabled])',
  '[tabindex]:not([tabindex="-1"])',
].join(',')

export function focusableWithin(container: HTMLElement): HTMLElement[] {
  return Array.from(container.querySelectorAll<HTMLElement>(FOCUSABLE)).filter(
    (element) => !element.hasAttribute('inert') && element.getAttribute('aria-hidden') !== 'true',
  )
}

/** Nächstes Fokusziel beim Tabben am Rand des Containers, sonst null (Browser übernimmt). */
export function wrapTarget(items: HTMLElement[], current: Element | null, backwards: boolean): HTMLElement | null {
  const first = items[0]
  const last = items[items.length - 1]
  if (!first || !last) return null
  if (backwards && (current === first || !items.includes(current as HTMLElement))) return last
  if (!backwards && (current === last || !items.includes(current as HTMLElement))) return first
  return null
}

/**
 * Hält den Tastaturfokus im Container, fokussiert beim Start `[autofocus]` bzw.
 * das erste Fokusziel und gibt den Fokus beim Beenden an das zuvor fokussierte
 * Element zurück. Liefert die Abmeldung.
 */
export function trapFocus(container: HTMLElement): () => void {
  const previous = document.activeElement instanceof HTMLElement ? document.activeElement : null
  function onKeydown(event: KeyboardEvent): void {
    if (event.key !== 'Tab') return
    const target = wrapTarget(focusableWithin(container), document.activeElement, event.shiftKey)
    if (!target) return
    event.preventDefault()
    target.focus()
  }
  const autofocus = container.querySelector<HTMLElement>('[autofocus]')
  ;(autofocus ?? focusableWithin(container)[0] ?? container).focus()
  document.addEventListener('keydown', onKeydown, true)
  return () => {
    document.removeEventListener('keydown', onKeydown, true)
    previous?.focus()
  }
}
