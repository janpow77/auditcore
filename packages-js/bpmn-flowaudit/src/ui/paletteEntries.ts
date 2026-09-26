/**
 * Icons of the core palette entries (ids of `@auditcore/bpmn-editor`). The
 * Vue palette shows our own icons and triggers the core entries, so no
 * palette styles of other editors are needed.
 */

import type { Role } from '../index'

export interface PaletteItem {
  id: string
  title: string
  icon: string
  group: string
  /** Role colours of „pool with role“ entries. */
  color?: { fill: string; stroke: string }
}

export const ROLE_ENTRY_PREFIX = 'flowaudit-pool-'

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
}

function item(id: string, entry: RawEntry, roles: readonly Role[]): PaletteItem {
  const base = { id, title: entry.title ?? id, group: entry.group ?? 'other' }
  const role = id.startsWith(ROLE_ENTRY_PREFIX) ? roles.find((candidate) => candidate.code === id.slice(ROLE_ENTRY_PREFIX.length)) : undefined
  return role ? { ...base, icon: role.icon, color: role.color } : { ...base, icon: CORE_ENTRY_ICONS[id] ?? '' }
}

/**
 * Palette entries of the running editor in display order (separators
 * dropped). Role entries get the icon and colours of their role, so no
 * markup of the diagram-js palette is rendered.
 */
export function readPaletteEntries(entries: Record<string, RawEntry>, roles: readonly Role[] = []): PaletteItem[] {
  return Object.entries(entries)
    .filter(([id, entry]) => !entry.separator && !id.startsWith('_'))
    .map(([id, entry]) => item(id, entry, roles))
}
