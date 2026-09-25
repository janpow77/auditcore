import { nextTick, onBeforeUnmount, watch, type Ref } from 'vue'

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
 * Hält den Tastaturfokus im Container, solange `active` wahr ist, und gibt ihn
 * danach an das zuvor fokussierte Element zurück.
 */
export function useFocusTrap(container: Ref<HTMLElement | null>, active: Ref<boolean>): void {
  let previous: HTMLElement | null = null

  function onKeydown(event: KeyboardEvent): void {
    const root = container.value
    if (event.key !== 'Tab' || !root) return
    const target = wrapTarget(focusableWithin(root), document.activeElement, event.shiftKey)
    if (target) {
      event.preventDefault()
      target.focus()
    }
  }

  async function activate(): Promise<void> {
    previous = document.activeElement instanceof HTMLElement ? document.activeElement : null
    await nextTick()
    const root = container.value
    if (!root) return
    const autofocus = root.querySelector<HTMLElement>('[autofocus]')
    ;(autofocus ?? focusableWithin(root)[0] ?? root).focus()
    document.addEventListener('keydown', onKeydown, true)
  }

  function deactivate(): void {
    document.removeEventListener('keydown', onKeydown, true)
    previous?.focus()
    previous = null
  }

  watch(active, (isActive) => (isActive ? void activate() : deactivate()), { immediate: true })
  onBeforeUnmount(deactivate)
}
