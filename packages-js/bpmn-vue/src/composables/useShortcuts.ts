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
