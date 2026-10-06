/**
 * Declarative toolbar entries: id, icon, label, group and whether the
 * action needs write access. `EditorToolbar` renders them and emits `action`.
 */

export type ToolbarAction =
  | 'save'
  | 'new'
  | 'import'
  | 'export'
  | 'undo'
  | 'redo'
  | 'zoom-in'
  | 'zoom-out'
  | 'fit'
  | 'info'
  | 'search'
  | 'minimap'
  | 'xml'
  | 'shortcuts'
  | 'validate'
  | 'validate-server'
  | 'enrich'
  | 'esi'
  | 'analysis'
  | 'share'
  | 'walkthrough'
  | 'compare'
  | 'key-filter'
  | 'decorations'
  | 'theme'
  | 'left-panel'
  | 'right-panel'

export interface ToolbarEntry {
  id: ToolbarAction
  icon: string
  label: string
  hint?: string
  writes?: boolean
}

export const FILE_ACTIONS: ToolbarEntry[] = [
  { id: 'new', icon: 'new', label: 'toolbar.new' },
  { id: 'import', icon: 'import', label: 'toolbar.import', writes: true },
  { id: 'export', icon: 'export', label: 'toolbar.export' },
  { id: 'info', icon: 'info', label: 'toolbar.info' },
]

export const EDIT_ACTIONS: ToolbarEntry[] = [
  { id: 'undo', icon: 'undo', label: 'toolbar.undo', writes: true },
  { id: 'redo', icon: 'redo', label: 'toolbar.redo', writes: true },
]

export const VIEW_ACTIONS: ToolbarEntry[] = [
  { id: 'zoom-out', icon: 'zoom-out', label: 'toolbar.zoomOut' },
  { id: 'zoom-in', icon: 'zoom-in', label: 'toolbar.zoomIn' },
  { id: 'fit', icon: 'fit', label: 'toolbar.fit' },
]

export const CHECK_ACTIONS: ToolbarEntry[] = [
  { id: 'validate', icon: 'validate', label: 'toolbar.validate', hint: 'toolbar.validateHint' },
  { id: 'validate-server', icon: 'validate', label: 'toolbar.validateServer', hint: 'toolbar.validateServerHint' },
  { id: 'enrich', icon: 'enrich', label: 'toolbar.enrich', hint: 'toolbar.enrichHint', writes: true },
  { id: 'esi', icon: 'marker-checkliste', label: 'toolbar.esi', hint: 'toolbar.esiHint' },
  { id: 'analysis', icon: 'analysis', label: 'toolbar.analysis', hint: 'toolbar.analysisHint' },
  { id: 'share', icon: 'share', label: 'toolbar.share' },
]

export const MODE_ACTIONS: ToolbarEntry[] = [
  { id: 'walkthrough', icon: 'play', label: 'toolbar.walkthrough' },
  { id: 'compare', icon: 'compare', label: 'toolbar.compare' },
  { id: 'key-filter', icon: 'filter', label: 'toolbar.keyFilter' },
  { id: 'search', icon: 'search', label: 'toolbar.search' },
  { id: 'minimap', icon: 'minimap', label: 'toolbar.minimap' },
  { id: 'decorations', icon: 'marker-pruefpunkt', label: 'toolbar.decorations' },
  { id: 'xml', icon: 'xml', label: 'toolbar.xml' },
  { id: 'shortcuts', icon: 'keyboard', label: 'toolbar.shortcuts' },
]

/** Whether a toolbar entry is disabled (writing actions when read-only, undo/redo by stack). */
export function actionDisabled(id: ToolbarAction, writes: boolean | undefined, state: { readonly: boolean; canUndo: boolean; canRedo: boolean }): boolean {
  return Boolean((writes && state.readonly) || (id === 'undo' && !state.canUndo) || (id === 'redo' && !state.canRedo))
}

/**
 * Action of the embedding application. The library only shows it and
 * reports the click (`host-action` / `onHostAction` with the id); what it
 * does is up to the host. `label` is shown as given (already translated).
 * Entries with `group: 'export'` appear in the export dialog, all others in
 * the „Prüfen“ menu of the toolbar – never as additional buttons.
 */
export interface HostAction {
  id: string
  label: string
  group?: 'export'
}

/** Action of the host per folder card of the collection overview (menu „Mehr“ of the card). */
export interface FolderAction {
  id: string
  label: string
}

/** Host actions of one place: `export` for the export dialog, `menu` for the toolbar menu. */
export function hostActionsFor(actions: readonly HostAction[] | undefined, place: 'export' | 'menu'): HostAction[] {
  return (actions ?? []).filter((action) => (place === 'export' ? action.group === 'export' : action.group !== 'export'))
}
