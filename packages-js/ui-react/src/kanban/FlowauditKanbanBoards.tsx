import { createBoardListController, relativeTime, selectBoardList, TEMPLATES, type Board, type BoardPort, type BoardSummary } from '@flowaudit/kanban-core'
import type { Locale } from '@flowaudit/ui-core'
import { forwardRef, useEffect, useImperativeHandle, useRef, useState, type FormEvent, type ReactElement } from 'react'
import { Button } from '../base/Button'
import { TextField } from '../base/TextField'
import { classes, useStoreState } from '../store'
import { useKanbanDialogText } from './text'

export interface FlowauditKanbanBoardsProps {
  port?: BoardPort | null
  activeId?: string
  now?: number
  locale?: Locale
  onBoardSelect?: (boardId: string) => void
  onCreated?: (board: Board) => void
}

export interface FlowauditKanbanBoardsHandle {
  reload: () => Promise<void>
}

type Text = ReturnType<typeof useKanbanDialogText>['t']
type List = ReturnType<typeof createBoardListController>

function CreateForm({ list, t, onCreated }: { list: List; t: Text; onCreated: (board: Board) => void }) {
  const [title, setTitle] = useState('')
  const [template, setTemplate] = useState('standard')
  const submit = async (event: FormEvent): Promise<void> => {
    event.preventDefault()
    const name = title.trim()
    if (!name) return
    const chosen = TEMPLATES.find((entry) => entry.key === template)
    const board = await list.create(name, chosen?.icon ?? '📋', template)
    if (board) onCreated(board)
  }
  return (
    <form className="fa-kanban-detail" onSubmit={(event) => void submit(event)}>
      <TextField value={title} label={t('boardTitle')} autoFocus required onChange={setTitle} />
      <div className="fa-kanban-boards__templates" role="group" aria-label={t('template')}>
        {TEMPLATES.map((entry) => (
          <button key={entry.key} type="button" className="fa-kanban-boards__template" aria-pressed={template === entry.key} onClick={() => setTemplate(entry.key)}>
            <span>{entry.icon} {entry.name}</span>
            <small className="fa-kanban-boards__sub">{entry.description}</small>
          </button>
        ))}
      </div>
      <Button type="submit" variant="primary">{t('create')}</Button>
    </form>
  )
}

interface ItemProps {
  summary: BoardSummary
  props: FlowauditKanbanBoardsProps
  list: List
  confirming: boolean
  onRemove: () => void
}

function OwnerTools({ summary, props, list, confirming, onRemove }: ItemProps) {
  const { t } = useKanbanDialogText(props.locale)
  return (
    <span className="fa-kanban-detail__row">
      <Button size="sm" variant="ghost" icon="pin" iconOnly pressed={summary.pinned} label={summary.pinned ? t('unpin') : t('pin')} onClick={() => void list.togglePin(summary)} />
      <Button size="sm" variant={confirming ? 'danger' : 'ghost'} icon="trash" iconOnly={!confirming} label={confirming ? t('confirmDeleteBoard', { title: summary.title }) : t('deleteBoard', { title: summary.title })} onClick={onRemove} />
    </span>
  )
}

function BoardItem({ summary, props, list, confirming, onRemove }: ItemProps) {
  const { t } = useKanbanDialogText(props.locale)
  const active = summary.id === (props.activeId ?? '')
  const age = relativeTime(summary.updated_at, props.now ?? Date.now())
  const role = summary.role !== 'owner' ? ` · ${t(`role_${summary.role}` as 'role_edit')}` : ''
  return (
    <li className={classes('fa-kanban-boards__item', active && 'is-active')}>
      <span aria-hidden="true">{summary.icon}</span>
      <button type="button" className="fa-kanban-boards__open" aria-current={active ? 'page' : undefined} onClick={() => props.onBoardSelect?.(summary.id)}>
        <span className="fa-kanban-boards__name">{summary.title}</span>
        <span className="fa-kanban-boards__sub">{t('tasksDone', { done: summary.stats.done, total: summary.stats.total })} · {age ? t(age.key, { count: age.count }) : ''}{role}</span>
        <span className="fa-kanban-toolbar__bar" aria-hidden="true"><span style={{ width: `${summary.stats.progress}%` }} /></span>
      </button>
      {summary.role === 'owner' ? <OwnerTools summary={summary} props={props} list={list} confirming={confirming} onRemove={onRemove} /> : null}
    </li>
  )
}

/** Boardliste wie `KanbanBoardList.vue` (eigene und geteilte Boards, Anheften, Löschen, Anlegen). */
export const FlowauditKanbanBoards = forwardRef<FlowauditKanbanBoardsHandle, FlowauditKanbanBoardsProps>(function FlowauditKanbanBoards(props, ref) {
  const { t } = useKanbanDialogText(props.locale)
  const port = useRef(props.port)
  port.current = props.port
  const [list] = useState(() => createBoardListController(() => port.current))
  const state = useStoreState(list.store)
  const view = selectBoardList(state)
  const [creating, setCreating] = useState(false)
  const [confirming, setConfirming] = useState<string | null>(null)
  useEffect(() => void list.load(), [list, props.port])
  useImperativeHandle(ref, () => ({ reload: list.load }), [list])
  const created = (board: Board): void => {
    setCreating(false)
    props.onCreated?.(board)
    props.onBoardSelect?.(board.id)
  }
  const remove = (summary: BoardSummary): void => {
    setConfirming(confirming === summary.id ? null : summary.id)
    if (confirming === summary.id) void list.remove(summary)
  }
  const groups = [{ key: 'myBoards', items: view.own }, { key: 'sharedBoards', items: view.shared }] as const
  return (
    <nav className="fa-kanban-boards" aria-label={t('boardsTitle')}>
      <div className="fa-kanban-detail__row" style={{ justifyContent: 'space-between' }}>
        <strong>{t('boardsTitle')}</strong>
        {list.canCreate() ? <Button size="sm" icon="plus" pressed={creating} onClick={() => setCreating(!creating)}>{t('newBoard')}</Button> : null}
      </div>
      {creating ? <CreateForm list={list} t={t} onCreated={created} /> : null}
      {state.error ? <p className="fa-field__note" role="alert">{state.error.message}</p> : null}
      {groups.map((group) => (
        <GroupList key={group.key} title={t(group.key)} mine={group.key === 'myBoards'} empty={t('noBoards')} loading={state.loading}>
          {group.items.map((summary) => <BoardItem key={summary.id} summary={summary} props={props} list={list} confirming={confirming === summary.id} onRemove={() => remove(summary)} />)}
        </GroupList>
      ))}
    </nav>
  )
})

function GroupList({ title, mine, empty, loading, children }: { title: string; mine: boolean; empty: string; loading: boolean; children: ReactElement[] }) {
  return (
    <>
      {children.length || mine ? <p className="fa-kanban-boards__group">{title}</p> : null}
      {mine && !children.length && !loading ? <p className="fa-kanban-settings__hint">{empty}</p> : null}
      <ul className="fa-kanban-boards__list">{children}</ul>
    </>
  )
}
