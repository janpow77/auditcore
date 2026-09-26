/**
 * Toolbar actions of the editor: dialogs and modes, colour, enrichment,
 * minimap, diagram info (apply, approve, new version) and export. Works on
 * an editor session; the resulting theme and suggestions live in `store`.
 */

import { applySuggestions, collectSuggestions, setColor, type DiagramInfo, type ExportChoice, type PaletteColor, type ProfileData, type RoleAlias, type Suggestion } from '../index'
import type { Theme } from './elementContract'
import type { Exporter } from './exporter'
import type { Translate } from './i18n/translator'
import type { EditorSession } from './session'
import { createStore } from './store'
import type { ToolbarAction } from './toolbarActions'
import { dialogPatch, toggleSidePatch, type DialogId, type SideView } from './uiState'

export interface ActionHandlers {
  save: () => void
  newDiagram: () => void
  analysis: () => void
  share: () => void
  excel: () => void
  approve: (info: DiagramInfo) => void
  message: (text: string) => void
}

export interface ActionOptions {
  profile: () => ProfileData | null
  roleAliases: () => RoleAlias[]
  exporter: Exporter
  t: Translate
}

export const THEMES: readonly Theme[] = ['auto', 'light', 'dark']

export interface ActionState {
  theme: Theme
  suggestions: Suggestion[]
}

export type EditorActions = ReturnType<typeof createEditorActions>

export const nextTheme = (theme: Theme): Theme => THEMES[(THEMES.indexOf(theme) + 1) % THEMES.length] ?? 'auto'

/** Diagram info (apply, approve, new version) and export. */
function infoActions(session: EditorSession, handlers: ActionHandlers, options: ActionOptions) {
  const { editor } = session

  /** Marks the diagram approved and hands it to the application (hash, immutable version). */
  function approve(info: DiagramInfo): void {
    const approved: DiagramInfo = { ...info, status: 'freigegeben', approvedOn: info.approvedOn || new Date().toISOString().slice(0, 10) }
    editor.setInfo(approved)
    handlers.approve(approved)
  }

  function newVersion(info: DiagramInfo): void {
    const version = String((Number.parseFloat(info.version ?? '1') || 1) + 1)
    editor.setInfo({ ...info, version, status: 'entwurf', approvedBy: undefined, approvedOn: undefined })
    handlers.message(options.t('collection.version', { version }))
  }

  async function runExport(choice: ExportChoice): Promise<void> {
    if (choice.format === 'excel') return handlers.excel()
    const result = await options.exporter.run(choice)
    const done = result.copied ? options.t('export.copied') : options.t('export.done', { format: options.t(`export.format.${choice.format}`) })
    handlers.message(result.neutralization ? `${done} ${options.t('export.report', { count: result.neutralization.replacements.length })}` : done)
  }

  return { applyInfo: (info: DiagramInfo) => editor.setInfo(info), approve, newVersion, runExport }
}

/** Shows or hides the core minimap (message if the editor has none). */
function toggleMinimap(session: EditorSession, handlers: ActionHandlers, options: ActionOptions): void {
  const minimap = session.editor.instance()?.get<{ toggle(open?: boolean): void; isOpen(): boolean }>('minimap', false)
  if (!minimap) {
    handlers.message(options.t('minimap.unavailable'))
    return
  }
  minimap.toggle()
  session.ui.set({ minimap: minimap.isOpen() })
}

function actionTable(session: EditorSession, handlers: ActionHandlers, toggle: { enrich: () => void; minimap: () => void; theme: () => void }): Record<ToolbarAction, () => void> {
  const { editor, validation, ui } = session
  const open = (id: DialogId) => () => ui.set(dialogPatch(ui.get(), id, true))
  const side = (view: SideView) => ui.set(toggleSidePatch(ui.get(), view))
  const flip = (key: 'leftOpen' | 'rightOpen' | 'filterOpen' | 'decorations') => () => session.updateUi({ [key]: !ui.get()[key] })
  return {
    save: handlers.save,
    new: handlers.newDiagram,
    import: () => undefined,
    export: open('export'),
    undo: () => editor.undo(),
    redo: () => editor.redo(),
    'zoom-in': () => editor.zoom(1.2),
    'zoom-out': () => editor.zoom(1 / 1.2),
    fit: () => editor.zoom('fit'),
    info: open('info'),
    search: open('search'),
    minimap: toggle.minimap,
    xml: open('xml'),
    shortcuts: open('shortcuts'),
    validate: () => (validation.runLocal(), side('issues')),
    'validate-server': () => (void validation.runServer(), side('issues')),
    enrich: toggle.enrich,
    esi: open('esi'),
    analysis: handlers.analysis,
    share: handlers.share,
    walkthrough: () => side('walkthrough'),
    compare: () => side('compare'),
    'key-filter': flip('filterOpen'),
    decorations: flip('decorations'),
    theme: toggle.theme,
    'left-panel': flip('leftOpen'),
    'right-panel': flip('rightOpen'),
  }
}

export function createEditorActions(session: EditorSession, handlers: ActionHandlers, options: ActionOptions) {
  const store = createStore<ActionState>({ theme: 'auto', suggestions: [] })
  const { editor, ui } = session

  function openEnrichment(): void {
    store.set({ suggestions: collectSuggestions(editor.model(), { profile: options.profile(), roleAliases: options.roleAliases() }) })
    ui.set(dialogPatch(ui.get(), 'enrich', true))
  }

  function applyEnrichment(accepted: Suggestion[], removePrefixes: boolean): void {
    const count = applySuggestions(editor.access(), accepted, { removePrefixes })
    handlers.message(options.t('enrich.applied', { count }))
  }

  const table = actionTable(session, handlers, {
    enrich: openEnrichment,
    minimap: () => toggleMinimap(session, handlers, options),
    theme: () => store.set((state) => ({ theme: nextTheme(state.theme) })),
  })

  function color(choice: PaletteColor | null): void {
    const selected = editor.services().selection?.get().filter((element) => !element.labelTarget) ?? []
    setColor(editor.services().modeling, selected, choice)
  }

  return {
    store,
    run: (action: ToolbarAction) => table[action](),
    color,
    applyEnrichment,
    setTheme: (theme: Theme) => store.set({ theme }),
    ...infoActions(session, handlers, options),
  }
}
