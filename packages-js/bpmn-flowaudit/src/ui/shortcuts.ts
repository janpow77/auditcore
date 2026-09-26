/**
 * Editor-level shortcuts in addition to the core's keyboard bindings:
 * Ctrl+S save, Ctrl+F element search, „?“ shortcut help.
 */

export interface ShortcutHandlers {
  save: () => void
  search: () => void
  help: () => void
}

function isTyping(target: EventTarget | null): boolean {
  const element = target as HTMLElement | null
  return Boolean(element && (element.isContentEditable || ['INPUT', 'TEXTAREA', 'SELECT'].includes(element.tagName)))
}

export function handleShortcut(event: KeyboardEvent, handlers: ShortcutHandlers): boolean {
  const ctrl = event.ctrlKey || event.metaKey
  const key = event.key.toLowerCase()
  if (ctrl && key === 's') {
    handlers.save()
  } else if (ctrl && key === 'f') {
    handlers.search()
  } else if (event.key === '?' && !isTyping(event.target)) {
    handlers.help()
  } else {
    return false
  }
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
  [['?'], 'shortcuts.help'],
]

/** Moves in a tab list for arrow keys, Home and End (WAI-ARIA tabs); `null` for other keys. */
export function tabMove(key: string, index: number, count: number): number | null {
  const moves: Record<string, number> = { ArrowRight: index + 1, ArrowDown: index + 1, ArrowLeft: index - 1, ArrowUp: index - 1, Home: 0, End: count - 1 }
  const move = moves[key]
  return move === undefined ? null : (move + count) % count
}
