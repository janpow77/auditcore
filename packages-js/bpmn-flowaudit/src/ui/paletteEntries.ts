/**
 * Icons of the core palette entries (ids of `@auditcore/bpmn-editor`). The
 * Vue palette shows our own icons and triggers the core entries, so no
 * palette styles of other editors are needed.
 */

import { label as localizedLabel, type Label, type Locale, type Role } from '../index'
import { browserStorage, readChoice, writePreference, type PreferenceStorage } from './preferences'

export interface PaletteItem {
  id: string
  title: string
  icon: string
  group: string
  /** Role colours of „pool with role“ entries. */
  color?: { fill: string; stroke: string }
  /** Short form of the role („VB“), only for „pool with role“ entries. */
  short?: string
  /** Long name of the role from the role catalogue of the profile. */
  roleLabel?: Label
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
  return role ? { ...base, icon: role.icon, color: role.color, short: role.short, roleLabel: role.label } : { ...base, icon: CORE_ENTRY_ICONS[id] ?? '' }
}

/**
 * Palette entries of the running editor in display order (separators
 * dropped). Role entries get the icon, colours, short form and long name of
 * their role, so no markup of the diagram-js palette is rendered.
 */
export function readPaletteEntries(entries: Record<string, RawEntry>, roles: readonly Role[] = []): PaletteItem[] {
  return Object.entries(entries)
    .filter(([id, entry]) => !entry.separator && !id.startsWith('_'))
    .map(([id, entry]) => item(id, entry, roles))
}

/** Display modes of the sections „Elemente“ and „Pool mit Rolle“. */
export const PALETTE_VIEWS = ['icons', 'tiles', 'list'] as const
export type PaletteView = (typeof PALETTE_VIEWS)[number]
export const PALETTE_VIEW_KEY = 'auditcore.bpmn.paletteView'

/** Stored palette view of this browser; `icons` when nothing (readable) is stored. */
export function readPaletteView(storage: PreferenceStorage | null = browserStorage()): PaletteView {
  return readChoice(PALETTE_VIEW_KEY, PALETTE_VIEWS, 'icons', storage)
}

/** Remembers the palette view locally (a blocked storage only loses the preference). */
export function writePaletteView(view: PaletteView, storage: PreferenceStorage | null = browserStorage()): void {
  writePreference(PALETTE_VIEW_KEY, view, storage)
}

/** Caption of an entry in tile view: role short form or element name. */
export function paletteCaption(item: PaletteItem, t: (key: string) => string): string {
  return item.short ?? paletteName(item, t)
}

/** Element name („Startereignis“) or long role name of an entry. */
export function paletteName(item: PaletteItem, t: (key: string) => string, locale: Locale = 'de'): string {
  if (item.roleLabel) return localizedLabel(item.roleLabel, locale)
  const key = `palette.item.${item.id}`
  const text = t(key)
  return text === key ? item.title : text
}
