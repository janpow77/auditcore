/**
 * Info column of the selected diagram: key info, tags, approvals and the
 * keyboard-accessible alternative to drag-and-drop („move to …“).
 */

import { Fragment, useState } from 'react'
import type { DiagramEntry, Tag } from '@auditcore/bpmn-flowaudit'
import { infoRows, toggledTags } from '@auditcore/bpmn-flowaudit/ui'
import { FaIcon } from '../base/FaIcon'
import { PromptDialog } from '../base/PromptDialog'
import { classes } from '../hooks'
import { useI18n } from '../i18n'
import type { CollectionBinding } from '../useCollection'

export interface DiagramInfoColumnProps {
  /** Collection binding from `useCollection` / `useCollectionBinding`. */
  store: CollectionBinding
  entry: DiagramEntry
  className?: string
  onOpen?: (id: string) => void
  onDeleted?: () => void
}

function Tags({ store, entry, tags, onNewTag }: { store: CollectionBinding; entry: DiagramEntry; tags: Tag[]; onNewTag: () => void }) {
  const { t } = useI18n()
  const toggleTag = (id: string) => void store.setTags(entry.id, toggledTags(entry, id))
  return (
    <>
      <div className="fa-info-column__tags">
        {tags.filter((item) => entry.tags.includes(item.id)).map((tag) => (
          <span key={tag.id} className="fa-chip" style={{ borderColor: tag.color }}><FaIcon name="tag" size={12} />{tag.name}</span>
        ))}
      </div>
      <details className="fa-info-column__more">
        <summary>{t('collection.tags')}</summary>
        <div className="fa-info-column__tags">
          {tags.map((tag) => (
            <button key={tag.id} type="button" className="fa-chip" aria-pressed={entry.tags.includes(tag.id)} onClick={() => toggleTag(tag.id)}>{tag.name}</button>
          ))}
          <button type="button" className="fa-chip" onClick={onNewTag}><FaIcon name="plus" size={12} />{t('collection.newTag')}</button>
        </div>
      </details>
    </>
  )
}

function Location({ store, entry }: { store: CollectionBinding; entry: DiagramEntry }) {
  const { t } = useI18n()
  return (
    <>
      <label className="fa-field">
        <span className="fa-label">{t('collection.moveTo')}</span>
        <select className="fa-select" value={entry.folderId ?? ''} onChange={(event) => void store.moveDiagram(entry.id, event.target.value || null)}>
          <option value="">{t('collection.topLevel')}</option>
          {[...store.state.collection.folders.values()].map((folder) => (
            <option key={folder.id} value={folder.id}>{folder.name}</option>
          ))}
        </select>
      </label>
      {entry.approvals.length ? (
        <div className="fa-info-column__approvals">
          <span className="fa-label">{t('collection.approvals')}</span>
          {entry.approvals.map((approval) => (
            <p key={approval.version} className="fa-help"><FaIcon name="lock" size={12} /> {approval.version} · {approval.approvedOn} · <code>{approval.sha256.slice(0, 16)}…</code></p>
          ))}
        </div>
      ) : null}
    </>
  )
}

export function DiagramInfoColumn({ store, entry, className, onOpen, onDeleted }: DiagramInfoColumnProps) {
  const { t, locale } = useI18n()
  const [renaming, setRenaming] = useState(false)
  const [tagging, setTagging] = useState(false)
  const tags = [...store.state.collection.tags.values()]

  const remove = async () => {
    if (!window.confirm(t('common.confirmDelete', { name: entry.name }))) return
    await store.removeDiagram(entry.id)
    onDeleted?.()
  }

  return (
    <section className={classes('fa-info-column', className)} aria-label={t('collection.info')}>
      <header className="fa-info-column__head">
        <h3>{entry.name}</h3>
        <button type="button" className="fa-btn fa-btn--primary" onClick={() => onOpen?.(entry.id)}><FaIcon name="folder-open" size={16} />{t('collection.open')}</button>
      </header>
      <dl className="fa-info-column__list">
        {infoRows(entry, t, locale).map(([term, value]) => (
          <Fragment key={term}>
            <dt>{term}</dt>
            <dd>{value}</dd>
          </Fragment>
        ))}
      </dl>
      <Tags store={store} entry={entry} tags={tags} onNewTag={() => setTagging(true)} />
      <Location store={store} entry={entry} />
      <div className="fa-info-column__actions">
        <button type="button" className="fa-btn" onClick={() => setRenaming(true)}><FaIcon name="new" size={16} />{t('collection.rename')}</button>
        <button type="button" className="fa-btn fa-btn--danger" onClick={() => void remove()}><FaIcon name="delete" size={16} />{t('common.delete')}</button>
      </div>
      <PromptDialog open={renaming} title={t('collection.rename')} label={t('collection.diagramName')} value={entry.name} onOpenChange={setRenaming} onConfirm={(name) => void store.renameDiagram(entry.id, name)} />
      <PromptDialog open={tagging} title={t('collection.newTag')} label={t('collection.tags')} onOpenChange={setTagging} onConfirm={(name) => void store.createTag(name)} />
    </section>
  )
}
