/**
 * Diagram collection as folder tree with drag-and-drop, search and filters
 * by status and tag (React counterpart of the Vue `CollectionTree`).
 */

import { useState, type DragEvent } from 'react'
import { DIAGRAM_STATUS, label } from '@auditcore/bpmn-flowaudit'
import { readDrag } from '@auditcore/bpmn-flowaudit/ui'
import { FaIcon } from '../base/FaIcon'
import { PromptDialog } from '../base/PromptDialog'
import { classes } from '../hooks'
import { useI18n } from '../i18n'
import type { CollectionBinding } from '../useCollection'
import { TreeFolder, type DropPayload } from './TreeFolder'

export interface CollectionTreeProps {
  /** Collection binding from `useCollection` / `useCollectionBinding`. */
  store: CollectionBinding
  selectedDiagram: string | null
  openDiagram: string | null
  onSelectDiagram?: (id: string | null) => void
  onOpenDiagram?: (id: string) => void
}

type PromptKind = 'folder' | 'diagram'

function Filters({ store }: { store: CollectionBinding }) {
  const { t, locale } = useI18n()
  const { filter, collection } = store.state
  return (
    <div className="fa-collection__filters">
      <input value={filter.search} className="fa-input" type="search" placeholder={t('common.search')} aria-label={t('common.search')} onChange={(event) => store.setFilter({ search: event.target.value })} />
      <div className="fa-grid-2">
        <select value={filter.status} className="fa-select" aria-label={t('collection.filter.status')} onChange={(event) => store.setFilter({ status: event.target.value })}>
          <option value="">{`${t('collection.filter.status')}: ${t('common.all')}`}</option>
          {Object.entries(DIAGRAM_STATUS).map(([code, text]) => (
            <option key={code} value={code}>{label(text, locale)}</option>
          ))}
        </select>
        <select value={filter.tag} className="fa-select" aria-label={t('collection.filter.tag')} onChange={(event) => store.setFilter({ tag: event.target.value })}>
          <option value="">{`${t('collection.filter.tag')}: ${t('common.all')}`}</option>
          {[...collection.tags.values()].map((tag) => (
            <option key={tag.id} value={tag.id}>{tag.name}</option>
          ))}
        </select>
      </div>
    </div>
  )
}

function Status({ store }: { store: CollectionBinding }) {
  const { t } = useI18n()
  const { error, loading, collection } = store.state
  return (
    <>
      {error ? <p className="fa-badge fa-badge--danger" role="alert">{error}</p> : null}
      {loading ? <p className="fa-help">{t('common.loading')}</p> : collection.diagrams.size === 0 ? <p className="fa-help fa-collection__empty">{t('collection.empty')}</p> : null}
    </>
  )
}

export function CollectionTree({ store, selectedDiagram, openDiagram, onSelectDiagram, onOpenDiagram }: CollectionTreeProps) {
  const { t } = useI18n()
  const [overRoot, setOverRoot] = useState(false)
  const [prompt, setPrompt] = useState<{ kind: PromptKind; open: boolean }>({ kind: 'folder', open: false })
  const selectedFolder = store.state.selectedFolder

  const create = async (name: string) => {
    if (prompt.kind === 'folder') {
      await store.createFolder(name, selectedFolder)
      return
    }
    const id = await store.createDiagram(name, selectedFolder)
    if (id) onOpenDiagram?.(id)
  }

  const onDrop = async (payload: DropPayload) => {
    if (payload.kind === 'diagram') await store.moveDiagram(payload.id, payload.target.folderId, payload.target.position)
    else await store.moveFolder(payload.id, payload.target.folderId)
  }

  const dropOnRoot = (event: DragEvent) => {
    event.preventDefault()
    setOverRoot(false)
    const payload = readDrag(event.nativeEvent)
    if (payload) void onDrop({ ...payload, target: { folderId: null } })
  }

  const selectFolder = (id: string | null) => {
    store.selectFolder(id)
    onSelectDiagram?.(null)
  }

  const isFolder = prompt.kind === 'folder'
  return (
    <nav className="fa-collection" aria-label={t('collection.label')}>
      <header className="fa-collection__head">
        <h2>{t('collection.label')}</h2>
        <button type="button" className="fa-icon-btn" title={t('collection.newFolder')} aria-label={t('collection.newFolder')} onClick={() => setPrompt({ kind: 'folder', open: true })}><FaIcon name="folder-new" /></button>
        <button type="button" className="fa-icon-btn" title={t('collection.newDiagram')} aria-label={t('collection.newDiagram')} onClick={() => setPrompt({ kind: 'diagram', open: true })}><FaIcon name="new" /></button>
      </header>
      <Filters store={store} />
      <Status store={store} />
      <div
        className={classes('fa-collection__root', overRoot && 'fa-tree__row--over', selectedFolder === null && 'fa-tree__row--selected')}
        onDragOver={(event) => (event.preventDefault(), setOverRoot(true))}
        onDragLeave={() => setOverRoot(false)}
        onDrop={dropOnRoot}
      >
        <button type="button" className="fa-tree__label" onClick={() => selectFolder(null)}><FaIcon name="overview" size={16} />{t('collection.topLevel')}</button>
      </div>
      <ul role="tree" className="fa-tree" aria-label={t('collection.label')}>
        <TreeFolder node={store.tree} depth={-1} selectedDiagram={selectedDiagram} selectedFolder={selectedFolder} openDiagram={openDiagram} onSelectDiagram={(id) => onSelectDiagram?.(id)} onOpenDiagram={(id) => onOpenDiagram?.(id)} onSelectFolder={selectFolder} onDrop={(payload) => void onDrop(payload)} />
      </ul>
      <PromptDialog
        open={prompt.open}
        title={isFolder ? t('collection.newFolder') : t('collection.newDiagram')}
        label={isFolder ? t('collection.folderName') : t('collection.diagramName')}
        onOpenChange={(open) => setPrompt((current) => ({ ...current, open }))}
        onConfirm={(name) => void create(name)}
      />
    </nav>
  )
}
