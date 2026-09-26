/**
 * One folder of the collection tree (recursive): collapsible, drop target
 * for diagrams and folders, rows draggable (tree pattern with ARIA).
 */

import { useState, type DragEvent } from 'react'
import type { DiagramEntry, FolderNode } from '@auditcore/bpmn-flowaudit'
import { readDrag, setDrag, statusBadge, statusText, type DropTarget } from '@auditcore/bpmn-flowaudit/ui'
import { FaIcon } from '../base/FaIcon'
import { classes } from '../hooks'
import { useI18n } from '../i18n'

export interface DropPayload {
  kind: 'diagram' | 'folder'
  id: string
  target: DropTarget
}

export interface TreeFolderProps {
  node: FolderNode
  depth: number
  selectedDiagram: string | null
  selectedFolder: string | null
  openDiagram: string | null
  onSelectDiagram: (id: string) => void
  onOpenDiagram: (id: string) => void
  onSelectFolder: (id: string | null) => void
  onDrop: (payload: DropPayload) => void
}

const allow = (event: DragEvent) => event.preventDefault()

function DiagramRow({ entry, index, props, drop }: { entry: DiagramEntry; index: number; props: TreeFolderProps; drop: (event: DragEvent, position?: number) => void }) {
  const { t, locale } = useI18n()
  const { selectedDiagram, openDiagram, depth } = props
  return (
    <li role="treeitem" aria-selected={selectedDiagram === entry.id}>
      <div
        className={classes('fa-tree__row', selectedDiagram === entry.id && 'fa-tree__row--selected', openDiagram === entry.id && 'fa-tree__row--open')}
        style={{ paddingLeft: `${(depth + 1) * 14 + 6}px` }}
        draggable="true"
        onDragStart={(event) => setDrag(event.nativeEvent, 'diagram', entry.id)}
        onDragOver={allow}
        onDrop={(event) => (event.preventDefault(), event.stopPropagation(), drop(event, index))}
      >
        <FaIcon name="grip" size={14} className="fa-tree__grip" />
        <button type="button" className="fa-tree__label" onClick={() => props.onSelectDiagram(entry.id)} onDoubleClick={() => props.onOpenDiagram(entry.id)} onKeyDown={(event) => event.key === 'Enter' && props.onOpenDiagram(entry.id)}>
          <FaIcon name="diagram" size={16} />
          <span className="fa-tree__name">{entry.name}</span>
        </button>
        <span className={classes('fa-badge', statusBadge(entry))}>{statusText(entry, t, locale)}</span>
      </div>
    </li>
  )
}

function FolderRow({ props, expanded, over, setExpanded, setOver, drop }: { props: TreeFolderProps; expanded: boolean; over: boolean; setExpanded: (value: boolean) => void; setOver: (value: boolean) => void; drop: (event: DragEvent) => void }) {
  const folder = props.node.folder
  if (!folder) return null
  return (
    <div
      className={classes('fa-tree__row fa-tree__row--folder', over && 'fa-tree__row--over', props.selectedFolder === folder.id && 'fa-tree__row--selected')}
      style={{ paddingLeft: `${props.depth * 14 + 6}px` }}
      draggable="true"
      onDragStart={(event) => setDrag(event.nativeEvent, 'folder', folder.id)}
      onDragOver={(event) => (event.preventDefault(), setOver(true))}
      onDragLeave={() => setOver(false)}
      onDrop={(event) => (event.preventDefault(), drop(event))}
    >
      <button type="button" className="fa-tree__toggle" aria-label={folder.name} onClick={() => setExpanded(!expanded)}>
        <FaIcon name={expanded ? 'chevron-down' : 'chevron-right'} size={14} />
      </button>
      <button type="button" className="fa-tree__label" onClick={() => props.onSelectFolder(folder.id)}>
        <FaIcon name={expanded ? 'folder-open' : 'folder'} size={16} />
        <span>{folder.name}</span>
      </button>
    </div>
  )
}

export function TreeFolder(props: TreeFolderProps) {
  const { node, depth } = props
  const [expanded, setExpanded] = useState(true)
  const [over, setOver] = useState(false)
  const folderId = node.folder?.id ?? null

  const drop = (event: DragEvent, position?: number) => {
    setOver(false)
    const payload = readDrag(event.nativeEvent)
    if (payload && payload.id !== folderId) props.onDrop({ ...payload, target: { folderId, position } })
  }

  return (
    <li role="treeitem" aria-expanded={node.folder ? expanded : undefined} className="fa-tree__folder">
      <FolderRow props={props} expanded={expanded} over={over} setExpanded={setExpanded} setOver={setOver} drop={drop} />
      <ul role="group" className="fa-tree__children" style={expanded ? undefined : { display: 'none' }}>
        {node.subfolders.map((child) => (
          <TreeFolder key={child.folder?.id} {...props} node={child} depth={depth + 1} />
        ))}
        {node.diagrams.map((entry, index) => (
          <DiagramRow key={entry.id} entry={entry} index={index} props={props} drop={drop} />
        ))}
      </ul>
    </li>
  )
}
