import { onBeforeUnmount, onMounted, type Ref } from 'vue'
import { listenBoardShortcuts, type BoardShortcut } from '@auditcore/kanban-core'

/** Tastenkürzel N, F und /, wenn der Fokus im Board oder auf der Seite (body) liegt. */
export function useBoardShortcuts(root: Ref<HTMLElement | null>, handle: (shortcut: BoardShortcut) => void): void {
  let stop: (() => void) | null = null
  onMounted(() => {
    stop = listenBoardShortcuts(() => root.value, handle)
  })
  onBeforeUnmount(() => stop?.())
}
