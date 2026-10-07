/**
 * Editor-level shortcuts in addition to the core's keyboard bindings:
 * Ctrl+S save, Ctrl+F element search, Ctrl+Alt+P properties panel,
 * „?“ shortcut help.
 */

export interface ShortcutHandlers {
  save: () => void
  search: () => void
  help: () => void
  /** Show or hide the properties panel (optional). */
  panel?: () => void
}

function isTyping(target: EventTarget | null): boolean {
  const element = target as HTMLElement | null
  return Boolean(element && (element.isContentEditable || ['INPUT', 'TEXTAREA', 'SELECT'].includes(element.tagName)))
}

/** Ctrl (Cmd) shortcuts by `KeyboardEvent.code`, with the Alt key they require. */
const CTRL_SHORTCUTS: [string, boolean, keyof ShortcutHandlers][] = [
  ['KeyS', false, 'save'],
  ['KeyF', false, 'search'],
  ['KeyP', true, 'panel'],
]

/** Handler for an event, or `undefined` when no editor shortcut matches. */
function shortcutFor(event: KeyboardEvent, handlers: ShortcutHandlers): (() => void) | undefined {
  if (event.ctrlKey || event.metaKey) {
    const key = event.key.toLowerCase()
    const match = CTRL_SHORTCUTS.find(([code, alt]) => (event.code === code || key === code.slice(3).toLowerCase()) && event.altKey === alt)
    return match ? handlers[match[2]] : undefined
  }
  return event.key === '?' && !isTyping(event.target) ? handlers.help : undefined
}

export function handleShortcut(event: KeyboardEvent, handlers: ShortcutHandlers): boolean {
  const handler = shortcutFor(event, handlers)
  if (!handler) return false
  handler()
  event.preventDefault()
  return true
}

/** Shortcut help table: keys (`@ctrl`, `@del` are translated) and message key. */
export const SHORTCUTS: [string[], string][] = [
  [['@ctrl', 'S'], 'shortcuts.save'],
  [['@ctrl', 'Z'], 'shortcuts.undo'],
  [['@ctrl', 'Y'], 'shortcuts.redo'],
  [['@ctrl', 'F'], 'shortcuts.search'],
  [['@ctrl', 'C', '@ctrl', 'V'], 'shortcuts.copy'],
  [['@ctrl', 'A'], 'shortcuts.selectAll'],
  [['@del'], 'shortcuts.delete'],
  [['E'], 'shortcuts.edit'],
  [['H'], 'shortcuts.hand'],
  [['L'], 'shortcuts.lasso'],
  [['S'], 'shortcuts.space'],
  [['C'], 'shortcuts.connect'],
  [['@ctrl', '+', '/', '−'], 'shortcuts.zoom'],
  [['@ctrl', '0'], 'shortcuts.fit'],
  [['@ctrl', '←', '→', '↑', '↓'], 'shortcuts.move'],
  [['←', '→', '↑', '↓'], 'shortcuts.moveElement'],
  [['@ctrl', 'Alt', 'P'], 'shortcuts.panel'],
  [['?'], 'shortcuts.help'],
]

/** Moves in a tab list for arrow keys, Home and End (WAI-ARIA tabs); `null` for other keys. */
export function tabMove(key: string, index: number, count: number): number | null {
  const moves: Record<string, number> = { ArrowRight: index + 1, ArrowDown: index + 1, ArrowLeft: index - 1, ArrowUp: index - 1, Home: 0, End: count - 1 }
  const move = moves[key]
  return move === undefined ? null : (move + count) % count
}
