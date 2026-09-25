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

export function useEditorActions(setup: Setup, handlers: ActionHandlers, options: ActionOptions) {
  const { editor, validation, ui } = setup
  const suggestions = shallowRef<Suggestion[]>([])
  const theme = shallowRef<Theme>('auto')

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
    minimap: () => toggleMinimap(),
    xml: () => (ui.dialogs.xml = true),
    shortcuts: () => (ui.dialogs.shortcuts = true),
    validate: () => (validation.runLocal(), toggleSide('issues')),
    'validate-server': () => (void validation.runServer(), toggleSide('issues')),
    enrich: () => openEnrichment(),
    esi: () => (ui.dialogs.esi = true),
    analysis: handlers.analysis,
    share: handlers.share,
    walkthrough: () => toggleSide('walkthrough'),
    compare: () => toggleSide('compare'),
    'key-filter': () => (ui.filterOpen = !ui.filterOpen),
    decorations: () => (ui.decorations = !ui.decorations),
    theme: () => (theme.value = THEMES[(THEMES.indexOf(theme.value) + 1) % THEMES.length]),
    'left-panel': () => (ui.leftOpen = !ui.leftOpen),
    'right-panel': () => (ui.rightOpen = !ui.rightOpen),
  }

  function toggleMinimap(): void {
    const minimap = editor.editor.value?.get<{ toggle(open?: boolean): void; isOpen(): boolean }>('minimap', false)
    if (!minimap) {
      handlers.message(options.t('minimap.unavailable'))
      return
    }
    minimap.toggle()
    ui.minimap = minimap.isOpen()
  }

  function openEnrichment(): void {
    suggestions.value = collectSuggestions(editor.model(), { profile: options.profile(), roleAliases: options.roleAliases() })
    ui.dialogs.enrich = true
  }

  function applyEnrichment(accepted: Suggestion[], removePrefixes: boolean): void {
    const count = applySuggestions(editor.access(), accepted, { removePrefixes })
    handlers.message(options.t('enrich.applied', { count }))
  }

  function color(choice: PaletteColor | null): void {
    const selected = editor.services().selection?.get().filter((element) => !element.labelTarget) ?? []
    setColor(editor.services().modeling, selected, choice)
  }

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

  return {
    run: (action: ToolbarAction) => ACTIONS[action](),
    color,
    suggestions,
    applyEnrichment,
    applyInfo,
    approve,
    newVersion,
    runExport,
    theme,
    emptyDiagram: EMPTY_DIAGRAM,
  }
}
