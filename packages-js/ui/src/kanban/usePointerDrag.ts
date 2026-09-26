/** Vue-Anbindung von `createPointerDrag` (Ziehen mit Maus, Stift und Touch). */
import { onBeforeUnmount, type Ref } from 'vue'
import { createPointerDrag } from '@flowaudit/kanban-core'
import { useStore } from '../composables/useStore'
import type { MoveController } from './useMoveController'

export { dropTarget, indexAt } from '@flowaudit/kanban-core'

export function usePointerDrag(mover: MoveController, root: Ref<HTMLElement | null>, enabled: () => boolean) {
  const pointer = createPointerDrag({ mover: mover.controller, root: () => root.value, enabled, columns: () => mover.columns.value })
  const drag = useStore(pointer.store)
  onBeforeUnmount(() => pointer.cancel())
  return { drag, onPointerDown: pointer.onPointerDown, consumeClick: pointer.consumeClick, cancel: pointer.cancel }
}

export type PointerDrag = ReturnType<typeof usePointerDrag>
