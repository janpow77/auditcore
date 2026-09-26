/** All dialogs of the editor, driven by the editor session and actions (Vue: `EditorDialogs.vue`). */

import { useEffect, useMemo, useState } from 'react'
import { collectExportData, type Approval, type ProcessModel, type ProfileSummary } from '@flowaudit/bpmn-flowaudit'
import { dialogPatch, elementNames, EMPTY_EXPORT_DATA, type DialogId, type EditorPorts } from '@flowaudit/bpmn-flowaudit/ui'
import { DiagramInfoDialog } from './dialogs/DiagramInfoDialog'
import { ElementSearch } from './dialogs/ElementSearch'
import { EnrichmentDialog } from './dialogs/EnrichmentDialog'
import { EsiDialog } from './dialogs/EsiDialog'
import { ExportDialog } from './dialogs/ExportDialog'
import { ShortcutHelp } from './dialogs/ShortcutHelp'
import { XmlDialog } from './dialogs/XmlDialog'
import { useStoreState } from './hooks'
import type { EditorRuntime } from './useEditorSession'

export interface EditorDialogsProps {
  runtime: EditorRuntime
  name: string
  diagramId?: string
  profiles: ProfileSummary[]
  approvals: Approval[]
  ports: EditorPorts
  onApplyXml: (xml: string) => void
}

/** Model snapshot for search/export/enrichment and XML for the XML view, taken when a dialog opens. */
function useDialogData(runtime: EditorRuntime) {
  const { dialogs } = useStoreState(runtime.ui)
  const { editor } = runtime.session
  const [model, setModel] = useState<ProcessModel | null>(null)
  const [xml, setXml] = useState('')
  const modelWanted = dialogs.search || dialogs.export || dialogs.enrich

  useEffect(() => {
    if (modelWanted && editor.store.get().ready) setModel(editor.model())
  }, [modelWanted, editor])

  useEffect(() => {
    if (dialogs.xml) void editor.exportXml().then(setXml)
  }, [dialogs.xml, editor])

  return { dialogs, model, xml }
}

export function EditorDialogs({ runtime, name, diagramId, profiles, approvals, ports, onApplyXml }: EditorDialogsProps) {
  const { dialogs, model, xml } = useDialogData(runtime)
  const { info } = useStoreState(runtime.session.editor.store)
  const { suggestions } = useStoreState(runtime.actions.store)
  const { editor } = runtime.session
  const { actions, ui } = runtime
  const exportData = useMemo(() => (model ? collectExportData(model) : EMPTY_EXPORT_DATA), [model])
  const names = useMemo(() => elementNames(model), [model])
  const setOpen = (id: DialogId) => (open: boolean) => ui.set(dialogPatch(ui.get(), id, open))
  const jump = (id: string) => void editor.select(id)

  return (
    <>
      <DiagramInfoDialog open={dialogs.info} info={info} profiles={profiles} approvals={approvals} fallbackTitle={name} onOpenChange={setOpen('info')} onApply={actions.applyInfo} onApprove={actions.approve} onNewVersion={actions.newVersion} />
      <ExportDialog open={dialogs.export} defaultTitle={info?.title || name} subtitle={info?.subtitle} data={exportData} confidentiality={info?.confidentiality} excel onOpenChange={setOpen('export')} onExport={(choice) => void actions.runExport(choice)} />
      <EnrichmentDialog open={dialogs.enrich} suggestions={suggestions} names={names} onOpenChange={setOpen('enrich')} onApply={actions.applyEnrichment} />
      <EsiDialog open={dialogs.esi} port={ports.esi} xml={editor.exportXml} diagramId={diagramId} onOpenChange={setOpen('esi')} onJump={jump} />
      <ElementSearch open={dialogs.search} model={model} onOpenChange={setOpen('search')} onJump={jump} />
      <ShortcutHelp open={dialogs.shortcuts} onOpenChange={setOpen('shortcuts')} />
      <XmlDialog open={dialogs.xml} xml={xml} readonly={runtime.isReadonly()} onOpenChange={setOpen('xml')} onApply={onApplyXml} />
    </>
  )
}
