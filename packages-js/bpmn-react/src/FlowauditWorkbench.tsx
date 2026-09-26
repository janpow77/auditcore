/**
 * Workbench: diagram collection (folder tree, info column, group overview)
 * plus editor – React counterpart of the Vue `FlowauditWorkbench`.
 * Persistence goes through the storage port.
 */

import { useEffect, useMemo, useRef, useState } from 'react'
import type { Comment, DiagramInfo, ProfileData, ProfileSummary, RoleAlias, StoragePort, ValidationPort } from '@flowaudit/bpmn-flowaudit'
import type { EditorFactory, EditorPorts, Locale } from '@flowaudit/bpmn-flowaudit/ui'
import { CollectionTree } from './collection/CollectionTree'
import { DiagramInfoColumn } from './collection/DiagramInfoColumn'
import { GroupOverview } from './collection/GroupOverview'
import { FlowauditEditor } from './FlowauditEditor'
import { classes } from './hooks'
import { I18nProvider, useI18n } from './i18n'
import { useCollection, type CollectionBinding } from './useCollection'
import '@flowaudit/bpmn-flowaudit/ui.css'

export interface FlowauditWorkbenchProps {
  storage: StoragePort
  profile?: ProfileData | null
  profiles?: ProfileSummary[]
  ports?: EditorPorts & { validation?: ValidationPort }
  locale?: Locale
  author?: string
  roleAliases?: RoleAlias[]
  editorFactory?: EditorFactory
  className?: string
  onOpen?: (id: string) => void
  onError?: (message: string) => void
}

interface OpenDiagram {
  id: string
  xml: string
  comments: Comment[]
}

/** Open, save and approve diagrams of the collection. */
function useWorkbench(store: CollectionBinding, props: FlowauditWorkbenchProps) {
  const { t } = useI18n()
  const [selected, setSelected] = useState<string | null>(null)
  const [opened, setOpened] = useState<OpenDiagram | null>(null)
  const [saving, setSaving] = useState(false)
  const dirty = useRef(false)

  const open = async (id: string) => {
    if (dirty.current && !window.confirm(t('workbench.discard'))) return
    const xml = await props.storage.loadDiagram(id)
    const comments = (await props.storage.loadComments?.(id)) ?? []
    dirty.current = false
    setOpened({ id, xml, comments })
    setSelected(id)
    props.onOpen?.(id)
  }

  const save = async (payload: { xml: string }) => {
    if (!opened) return
    setSaving(true)
    await store.saveDiagram(opened.id, payload.xml)
    await props.storage.saveComments?.(opened.id, opened.comments)
    setSaving(false)
    dirty.current = false
  }

  const approve = async (payload: { xml: string; info: DiagramInfo }) => {
    if (!opened) return
    await save(payload)
    await store.approveDiagram(opened.id, payload.xml, payload.info.version ?? '1', { approvedBy: payload.info.approvedBy, approvedOn: payload.info.approvedOn, cutoffDate: payload.info.systemCutoffDate })
  }

  const createAndOpen = async () => {
    const id = await store.createDiagram(t('collection.newDiagram'), store.state.selectedFolder)
    if (id) await open(id)
  }

  const onXml = (xml: string) => {
    if (!opened || xml === opened.xml) return
    dirty.current = true
    setOpened({ ...opened, xml })
  }

  const onDeleted = () => {
    if (opened?.id === selected) setOpened(null)
    setSelected(null)
  }

  return { selected, setSelected, opened, setOpened, saving, open, save, approve, createAndOpen, onXml, onDeleted }
}

type Bench = ReturnType<typeof useWorkbench>

function EditorPane({ store, bench, props, opened }: { store: CollectionBinding; bench: Bench; props: FlowauditWorkbenchProps; opened: OpenDiagram }) {
  const entry = store.entry(opened.id)
  const { collection, revision } = store.state
  const { storage } = props
  const compareSources = useMemo(
    () => (void revision, [...collection.diagrams.values()].filter((item) => item.id !== opened.id).map((item) => ({ id: item.id, name: item.name, load: () => storage.loadDiagram(item.id) }))),
    [collection, revision, opened.id, storage],
  )
  if (!entry) return null
  return (
    <FlowauditEditor
      key={entry.id}
      xml={opened.xml}
      name={entry.name}
      diagramId={entry.id}
      profile={props.profile ?? null}
      profiles={props.profiles ?? []}
      ports={props.ports ?? {}}
      locale={props.locale ?? 'de'}
      comments={opened.comments}
      approvals={entry.approvals}
      author={props.author ?? ''}
      compareSources={compareSources}
      roleAliases={props.roleAliases ?? []}
      saving={bench.saving}
      editorFactory={props.editorFactory}
      onXmlChange={bench.onXml}
      onNameChange={(name) => void store.renameDiagram(entry.id, name)}
      onCommentsChange={(comments) => bench.setOpened({ ...opened, comments })}
      onSave={(payload) => void bench.save(payload)}
      onApprove={(payload) => void bench.approve(payload)}
      onNew={() => void bench.createAndOpen()}
    />
  )
}

function OverviewPane({ store, bench, profile }: { store: CollectionBinding; bench: Bench; profile: ProfileData | null }) {
  const { t } = useI18n()
  const { collection, selectedFolder } = store.state
  const selectedEntry = bench.selected ? store.entry(bench.selected) : undefined
  const folderTitle = selectedFolder ? (collection.folders.get(selectedFolder)?.name ?? '') : t('collection.topLevel')
  return (
    <div className="fa-workbench__overview">
      <GroupOverview overview={store.overview} profile={profile} issues={store.issues} title={folderTitle} onOpen={(id) => void bench.open(id)} />
      {selectedEntry ? <DiagramInfoColumn className="fa-workbench__info" store={store} entry={selectedEntry} onOpen={(id) => void bench.open(id)} onDeleted={bench.onDeleted} /> : null}
    </div>
  )
}

/** Reports collection errors to `onError`. */
function useErrorReport(error: string | null, onError?: (message: string) => void): void {
  const latest = useRef(onError)
  useEffect(() => {
    latest.current = onError
  })
  useEffect(() => {
    if (error) latest.current?.(error)
  }, [error])
}

function Workbench(props: FlowauditWorkbenchProps) {
  const store = useCollection(props.storage)
  const bench = useWorkbench(store, props)
  const { opened } = bench
  useErrorReport(store.state.error, props.onError)
  const openEntry = opened ? store.entry(opened.id) : undefined

  return (
    <div className={classes('fa-root fa-workbench', props.className)} lang={props.locale ?? 'de'}>
      <aside className="fa-workbench__side">
        <CollectionTree store={store} selectedDiagram={bench.selected} openDiagram={opened?.id ?? null} onSelectDiagram={bench.setSelected} onOpenDiagram={(id) => void bench.open(id)} />
      </aside>
      <main className="fa-workbench__main">
        {opened && openEntry ? <EditorPane store={store} bench={bench} props={props} opened={opened} /> : <OverviewPane store={store} bench={bench} profile={props.profile ?? null} />}
      </main>
    </div>
  )
}

export function FlowauditWorkbench(props: FlowauditWorkbenchProps) {
  return (
    <I18nProvider locale={props.locale ?? 'de'}>
      <Workbench {...props} />
    </I18nProvider>
  )
}
