import { nextTick, onBeforeUnmount, watch, type Ref } from 'vue'
import { createFocusTrap } from '@flowaudit/ui-core'

/** Seit 0.3.0 aus `@flowaudit/ui-core` (gemeinsam mit der React-Fassung). */
export { focusableWithin, wrapTarget } from '@flowaudit/ui-core'

/**
 * Hält den Tastaturfokus im Container, solange `active` wahr ist, und gibt ihn
 * danach an das zuvor fokussierte Element zurück.
 */
export function useFocusTrap(container: Ref<HTMLElement | null>, active: Ref<boolean>): void {
  const trap = createFocusTrap(() => container.value)
  watch(
    active,
    async (isActive) => {
      if (!isActive) return trap.deactivate()
      await nextTick()
      trap.activate()
    },
    { immediate: true },
  )
  onBeforeUnmount(trap.deactivate)
}
