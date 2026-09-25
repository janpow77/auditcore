import { onBeforeUnmount, onMounted, type Ref } from 'vue'
import { boardShortcut, type BoardShortcut } from './cardKeys'

/** Tastenkürzel N, F und /, wenn der Fokus im Board oder auf der Seite (body) liegt. */
export function useBoardShortcuts(root: Ref<HTMLElement | null>, handle: (shortcut: BoardShortcut) => void): void {
  function onKeydown(event: KeyboardEvent): void {
    const focus = document.activeElement
    const inside = focus === document.body || (focus !== null && root.value?.contains(focus))
    const shortcut = inside ? boardShortcut(event) : null
    if (!shortcut) return
    event.preventDefault()
    handle(shortcut)
  }
  onMounted(() => document.addEventListener('keydown', onKeydown))
  onBeforeUnmount(() => document.removeEventListener('keydown', onKeydown))
}
