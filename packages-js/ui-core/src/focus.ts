/** Fokusfalle für Dialoge (framework-frei, von Vue und React genutzt). */
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

export interface FocusTrap {
  /** Fokus in den Container (Element mit `autofocus`, sonst erstes fokussierbares) und Tab-Taste einfangen. */
  activate: () => void
  /** Falle lösen und den Fokus an das vorher fokussierte Element zurückgeben. */
  deactivate: () => void
}

export function createFocusTrap(container: () => HTMLElement | null): FocusTrap {
  let previous: HTMLElement | null = null
  let active = false

  function onKeydown(event: KeyboardEvent): void {
    const root = container()
    if (event.key !== 'Tab' || !root) return
    const target = wrapTarget(focusableWithin(root), document.activeElement, event.shiftKey)
    if (target) {
      event.preventDefault()
      target.focus()
    }
  }

  return {
    activate() {
      const root = container()
      if (!root || active) return
      active = true
      previous = document.activeElement instanceof HTMLElement ? document.activeElement : null
      const autofocus = root.querySelector<HTMLElement>('[autofocus]')
      ;(autofocus ?? focusableWithin(root)[0] ?? root).focus()
      document.addEventListener('keydown', onKeydown, true)
    },
    deactivate() {
      if (!active) return
      active = false
      document.removeEventListener('keydown', onKeydown, true)
      previous?.focus()
      previous = null
    },
  }
}
