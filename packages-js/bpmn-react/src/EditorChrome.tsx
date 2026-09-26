/** Toolbar, palette, key filter, side panel and status bar of the React editor. */

import { profileReference, type Direction, type PaletteColor } from '@auditcore/bpmn-flowaudit'
import { activeActions, filterKeys, readImportFile, type UiState } from '@auditcore/bpmn-flowaudit/ui'
import { StatusBar } from './canvas/CanvasParts'
import { useEditorState, useValidationView } from './context'
import type { FlowauditEditorProps } from './editorProps'
import { EditorSidePanel } from './EditorSidePanel'
import { useStoreState } from './hooks'
import { useI18n } from './i18n'
import { ToolPalette } from './palette/ToolPalette'
import { EditorToolbar } from './toolbar/EditorToolbar'
import type { EditorRuntime } from './useEditorSession'
import { KeyFilterBar } from './views/KeyFilterBar'

interface PartProps {
  runtime: EditorRuntime | null
  props: FlowauditEditorProps
  ui: UiState
  readonly: boolean
}

/** Parts render only once the session exists (the canvas host is always there). */
export function EditorChrome(parts: PartProps) {
  return parts.runtime ? <Toolbar {...parts} runtime={parts.runtime} /> : null
}

function Toolbar({ runtime, props, ui, readonly }: PartProps & { runtime: EditorRuntime }) {
  const state = useEditorState()
  const { session, actions } = runtime
  const importFile = async (file: File) => {
    const imported = await readImportFile(file)
    props.onXmlChange?.(imported.xml)
    if (!props.name) props.onNameChange?.(imported.name)
  }
  return (
    <EditorToolbar
      name={props.name ?? ''}
      dirty={state.dirty}
      saving={Boolean(props.saving)}
      readonly={readonly}
      canUndo={state.canUndo}
      canRedo={state.canRedo}
      direction={ui.direction}
      pageView={ui.pageView}
      active={activeActions(ui)}
      hidden={props.hiddenActions ?? []}
      palette={props.palette}
      onAction={actions.run}
      onNameChange={props.onNameChange}
      onColor={(color: PaletteColor | null) => actions.color(color)}
      onDirection={(direction: Direction) => session.setDirection(direction)}
      onPageView={(pageView) => session.updateUi({ pageView })}
      onImportFile={(file) => void importFile(file)}
    />
  )
}

function Palette({ runtime, readonly }: { runtime: EditorRuntime; readonly: boolean }) {
  const { palette } = useStoreState(runtime.session.canvas)
  return <ToolPalette items={palette} disabled={readonly} onTrigger={runtime.session.trigger} />
}

function Filter({ runtime, ui }: { runtime: EditorRuntime; ui: UiState }) {
  useEditorState()
  const { session } = runtime
  return (
    <KeyFilterBar
      kind={ui.filterKind}
      value={ui.filterValue}
      keys={filterKeys(session, ui.filterOpen)}
      hits={ui.filterHits}
      onKindChange={(filterKind) => session.updateUi({ filterKind })}
      onValueChange={(filterValue) => session.updateUi({ filterValue })}
      onClear={() => session.updateUi({ filterValue: '', filterOpen: false })}
    />
  )
}

export function EditorSide({ runtime, props, ui, readonly, part }: PartProps & { part: 'palette' | 'filter' | 'side' }) {
  if (!runtime) return null
  if (part === 'palette') return ui.leftOpen ? <Palette runtime={runtime} readonly={readonly} /> : null
  if (part === 'filter') return ui.filterOpen ? <Filter runtime={runtime} ui={ui} /> : null
  if (!ui.rightOpen) return null
  return (
    <EditorSidePanel
      view={ui.side}
      comments={props.comments ?? []}
      author={props.author ?? ''}
      compareSources={props.compareSources ?? []}
      palette={props.palette}
      onViewChange={(side) => runtime.ui.set({ side })}
      onCommentsChange={props.onCommentsChange}
      onJump={(id) => runtime.session.editor.select(id)}
    />
  )
}

export function EditorFooter(parts: PartProps) {
  return parts.runtime ? <Footer {...parts} runtime={parts.runtime} /> : null
}

function Footer({ runtime, props, ui }: PartProps & { runtime: EditorRuntime }) {
  const { t } = useI18n()
  const state = useEditorState()
  const validation = useValidationView()
  return (
    <StatusBar
      scale={state.scale}
      count={validation.count}
      profile={props.profile ? profileReference(props.profile) : undefined}
      message={t(ui.message)}
      onIssues={() => runtime.ui.set({ side: 'issues', rightOpen: true })}
    />
  )
}
