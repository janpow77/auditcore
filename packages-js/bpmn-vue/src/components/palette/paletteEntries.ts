/**
 * Icons of the core palette entries (ids of `@flowaudit/bpmn-editor`). The
 * Vue palette shows our own icons and triggers the core entries, so no
 * palette styles of other editors are needed.
 */

export interface PaletteItem {
  id: string
  title: string
  icon: string
  group: string
  html?: string
}

export const CORE_ENTRY_ICONS: Record<string, string> = {
  'hand-tool': 'hand',
  'lasso-tool': 'lasso',
  'space-tool': 'space',
  'global-connect-tool': 'connect',
  'create.start-event': 'bpmn-start',
  'create.intermediate-event': 'bpmn-intermediate',
  'create.end-event': 'bpmn-end',
  'create.exclusive-gateway': 'bpmn-gateway',
  'create.task': 'bpmn-task',
  'create.subprocess-expanded': 'bpmn-subprocess',
  'create.data-object': 'bpmn-data-object',
  'create.data-store': 'bpmn-data-store',
  'create.participant-expanded': 'bpmn-pool',
  'create.group': 'bpmn-group',
  'create.text-annotation': 'bpmn-annotation',
}

interface RawEntry {
  group?: string
  title?: string
  separator?: boolean
  html?: string
}

/** Palette entries of the running editor in display order (separators dropped). */
export function readPaletteEntries(entries: Record<string, RawEntry>): PaletteItem[] {
  return Object.entries(entries)
    .filter(([id, entry]) => !entry.separator && !id.startsWith('_'))
    .map(([id, entry]) => ({ id, title: entry.title ?? id, group: entry.group ?? 'other', icon: CORE_ENTRY_ICONS[id] ?? '', html: entry.html }))
}
