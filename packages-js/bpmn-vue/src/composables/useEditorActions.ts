/**
 * Toolbar actions of the editor: dialogs and modes, colour, enrichment,
 * key filter, diagram info (apply, approve, new version) and export.
 */

import { shallowRef, watch } from 'vue'
import {
  applySuggestions,
  collectSuggestions,
  elementsForKey,
  EMPTY_DIAGRAM,
  setColor,
  type DiagramInfo,
  type ExportChoice,
  type FlowauditHighlight,
  type PaletteColor,
  type ProfileData,
  type RoleAlias,
  type Suggestion,
} from '@flowaudit/bpmn-flowaudit'
import type { ToolbarAction } from '../components/toolbar/toolbarActions'
import type { useEditorSetup } from './useEditorSetup'
import type { useExport } from './useExport'

type Setup = ReturnType<typeof useEditorSetup>

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
  exporter: ReturnType<typeof useExport>
  t: (key: string, params?: Record<string, string | number>) => string
}

const THEMES = ['auto', 'light', 'dark'] as const
export type Theme = (typeof THEMES)[number]

/** Enrichment: collect suggestions for the dialog and apply the accepted ones. */
function enrichmentActions(setup: Setup, handlers: ActionHandlers, options: ActionOptions) {
  const { editor, ui } = setup
  const suggestions = shallowRef<Suggestion[]>([])

  function openEnrichment(): void {
    suggestions.value = collectSuggestions(editor.model(), { profile: options.profile(), roleAliases: options.roleAliases() })
    ui.dialogs.enrich = true
  }

  function applyEnrichment(accepted: Suggestion[], removePrefixes: boolean): void {
    const count = applySuggestions(editor.access(), accepted, { removePrefixes })
    handlers.message(options.t('enrich.applied', { count }))
  }

  return { suggestions, openEnrichment, applyEnrichment }
}

/** Diagram info (apply, approve, new version) and export. */
function infoActions(setup: Setup, handlers: ActionHandlers, options: ActionOptions) {
  const { editor } = setup

  function applyInfo(info: DiagramInfo): void {
    editor.setInfo(info)
  }

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

  return { applyInfo, approve, newVersion, runExport }
}

/** Highlights the elements matching the key filter whenever filter or model change. */
function watchKeyFilter(setup: Setup): void {
  const { editor, ui } = setup

  function highlightKey(): void {
    const layer = editor.editor.value?.get<FlowauditHighlight>('flowauditHighlight', false)
    if (!layer || !editor.state.ready) return
    if (!ui.filterOpen || !ui.filterValue.trim()) {
      layer.clear('filter')
      ui.filterHits = 0
      return
    }
    ui.filterHits = layer.filter(elementsForKey(editor.model(), ui.filterKind, ui.filterValue))
  }

  watch(() => [ui.filterOpen, ui.filterKind, ui.filterValue, editor.state.changes], highlightKey)

}

/** Shows or hides the core minimap (message if the editor has none). */
function toggleMinimap(setup: Setup, handlers: ActionHandlers, options: ActionOptions): void {
  const { editor, ui } = setup
  const minimap = editor.editor.value?.get<{ toggle(open?: boolean): void; isOpen(): boolean }>('minimap', false)
  if (!minimap) {
    handlers.message(options.t('minimap.unavailable'))
    return
  }
  minimap.toggle()
  ui.minimap = minimap.isOpen()
}

export function useEditorActions(setup: Setup, handlers: ActionHandlers, options: ActionOptions) {
  const { editor, validation, ui } = setup
  const theme = shallowRef<Theme>('auto')

  const enrichment = enrichmentActions(setup, handlers, options)
  const info = infoActions(setup, handlers, options)
  watchKeyFilter(setup)

  const toggleSide = (view: typeof ui.side) => {
    ui.side = ui.side === view && ui.rightOpen ? 'properties' : view
    ui.rightOpen = true
  }

  const ACTIONS: Record<ToolbarAction, () => void> = {
    save: handlers.save,
    new: handlers.newDiagram,
    import: () => undefined,
    export: () => (ui.dialogs.export = true),
    undo: () => editor.undo(),
    redo: () => editor.redo(),
    'zoom-in': () => editor.zoom(1.2),
    'zoom-out': () => editor.zoom(1 / 1.2),
    fit: () => editor.zoom('fit'),
    info: () => (ui.dialogs.info = true),
    search: () => (ui.dialogs.search = true),
    minimap: () => toggleMinimap(setup, handlers, options),
    xml: () => (ui.dialogs.xml = true),
    shortcuts: () => (ui.dialogs.shortcuts = true),
    validate: () => (validation.runLocal(), toggleSide('issues')),
    'validate-server': () => (void validation.runServer(), toggleSide('issues')),
    enrich: () => enrichment.openEnrichment(),
    esi: () => (ui.dialogs.esi = true),
    analysis: handlers.analysis,
    share: handlers.share,
    walkthrough: () => toggleSide('walkthrough'),
    compare: () => toggleSide('compare'),
    'key-filter': () => (ui.filterOpen = !ui.filterOpen),
    decorations: () => (ui.decorations = !ui.decorations),
    theme: () => (theme.value = THEMES[(THEMES.indexOf(theme.value) + 1) % THEMES.length] ?? 'auto'),
    'left-panel': () => (ui.leftOpen = !ui.leftOpen),
    'right-panel': () => (ui.rightOpen = !ui.rightOpen),
  }

  function color(choice: PaletteColor | null): void {
    const selected = editor.services().selection?.get().filter((element) => !element.labelTarget) ?? []
    setColor(editor.services().modeling, selected, choice)
  }

  return {
    run: (action: ToolbarAction) => ACTIONS[action](),
    color,
    suggestions: enrichment.suggestions,
    applyEnrichment: enrichment.applyEnrichment,
    ...info,
    theme,
    emptyDiagram: EMPTY_DIAGRAM,
  }
}
