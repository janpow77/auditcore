import type { Ref } from 'vue'
import { focusRow, navigationDirection, type SynopsisController, type SynopsisSelection } from '@auditcore/ui-core'

export { focusRow } from '@auditcore/ui-core'

export interface UseSynopsisNavigation {
  go: (direction: 1 | -1) => string | null
  onKeydown: (event: KeyboardEvent) => void
}

/** Navigation zwischen Änderungen mit Schaltflächen und Tasten N/J bzw. P/K. */
export function useSynopsisNavigation(
  controller: SynopsisController,
  selection: Readonly<Ref<SynopsisSelection>>,
  root: Ref<HTMLElement | null>,
  onNavigate: (id: string) => void,
): UseSynopsisNavigation {
  function go(direction: 1 | -1): string | null {
    const next = controller.go(selection.value, direction)
    if (next === null) return null
    focusRow(root.value, next)
    onNavigate(next)
    return next
  }

  function onKeydown(event: KeyboardEvent): void {
    const direction = navigationDirection(event)
    if (direction === null) return
    go(direction)
    event.preventDefault()
  }

  return { go, onKeydown }
}
