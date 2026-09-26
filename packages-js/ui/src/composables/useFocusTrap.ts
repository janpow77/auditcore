import { nextTick, onBeforeUnmount, watch, type Ref } from 'vue'
import { trapFocus } from '@flowaudit/ui-core'

/** Reine Fokushilfen aus `@flowaudit/ui-core` (auch von der React-Fassung genutzt). */
export { focusableWithin, wrapTarget } from '@flowaudit/ui-core'

/**
 * Hält den Tastaturfokus im Container, solange `active` wahr ist, und gibt ihn
 * danach an das zuvor fokussierte Element zurück.
 */
export function useFocusTrap(container: Ref<HTMLElement | null>, active: Ref<boolean>): void {
  let release: (() => void) | null = null

  async function activate(): Promise<void> {
    await nextTick()
    const root = container.value
    if (root && !release) release = trapFocus(root)
  }

  function deactivate(): void {
    release?.()
    release = null
  }

  watch(active, (isActive) => (isActive ? void activate() : deactivate()), { immediate: true })
  onBeforeUnmount(deactivate)
}
