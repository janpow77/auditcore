/**
 * Natives React-Kanban-Board wie `KanbanBoard.vue`: gleiche Props, Ereignisse
 * (als `onXyz`), gleiches Markup und dieselbe Kernlogik aus
 * `@auditcore/kanban-core` (Board-, Verschiebe- und Zeiger-Controller).
 */
import { doneColumn, findCard, handleCardKey, type Attachment, type Board, type BoardPort, type Card, type CardLink, type KanbanError, type UserRef } from '@auditcore/kanban-core'
import type { Locale } from '@auditcore/ui-core'
import { forwardRef, useImperativeHandle, useRef, useState, type KeyboardEvent, type ReactNode } from 'react'
import { Button } from '../base/Button'
import { Icon } from '../base/Icon'
import { useElementId } from '../store'
import { BoardDialogs } from './BoardDialogs'
import { KanbanCard } from './KanbanCard'
import { KanbanColumn } from './KanbanColumn'
import { KanbanToolbar } from './KanbanToolbar'
import { useKanbanText } from './text'
import { useBoard, useBoardShortcuts, useMover, type BoardBinding } from './useKanbanBoard'

export interface FlowauditKanbanBoardProps {
  /** Speicher-/Rechte-Port; ohne Port wird `board` lokal (In-Memory) bearbeitet. */
  port?: BoardPort | null
  boardId?: string
  board?: Board | null
  userId?: string
  users?: readonly UserRef[]
  readOnly?: boolean
  sharedByName?: string
  showFullscreen?: boolean
  today?: string
  locale?: Locale
  /** Zusatzinhalt in der Detailansicht (Slot `card-extra` in Vue). */
  renderCardExtra?: (card: Card) => ReactNode
  onBoardChange?: (board: Board) => void
  onError?: (error: KanbanError) => void
  onFullscreen?: () => void
  onNavigate?: (link: CardLink, card: Card) => void
  onAttachment?: (attachment: Attachment, card: Card) => void
  onCardOpen?: (card: Card) => void
}

/** Methoden über `ref` (wie `defineExpose` der Vue-Fassung). */
export interface FlowauditKanbanBoardHandle {
  reload: () => Promise<void>
  board: Board | null
}

type Mover = ReturnType<typeof useMover>

function StatusLines({ props, binding, announcement, instructionsId }: { props: FlowauditKanbanBoardProps; binding: BoardBinding; announcement: string; instructionsId: string }) {
  const { t } = useKanbanText(props.locale)
  const { state, view } = binding
  const readOnlyView = state.board !== null && !view.can.edit && !view.can.move
  const shared = props.sharedByName ? `${t('sharedBy', { name: props.sharedByName })} – ` : ''
  return (
    <>
      <p id={instructionsId} className="fa-sr-only">{t('moveInstructions')}</p>
      <p className="fa-sr-only" role="status" aria-live="polite" aria-atomic="true">{announcement}</p>
      {readOnlyView ? <div className="fa-kanban__banner"><Icon name="lock" size={16} /> {shared}{t('readOnly')}</div> : null}
      {state.error ? (
        <div className="fa-kanban__error" role="alert">
          {t('errorPrefix', { message: state.error.message })}
          {state.board ? null : <Button size="sm" onClick={() => void binding.controller.load()}>{t('retry')}</Button>}
        </div>
      ) : null}
      {state.loading && !state.board ? <p className="fa-kanban__loading">{t('loading')}</p> : null}
    </>
  )
}

interface ColumnsProps {
  props: FlowauditKanbanBoardProps
  binding: BoardBinding
  motion: Mover
  instructionsId: string
  onAdd: (columnId: string) => void
  onOpen: (card: Card) => void
}

function Columns({ props, binding, motion, instructionsId, onAdd, onOpen }: ColumnsProps) {
  const { t } = useKanbanText(props.locale)
  const board = binding.state.board as Board
  const { can, today } = binding.view
  const onCardKey = (event: KeyboardEvent<HTMLElement>, card: Card): void => {
    if (handleCardKey(event, card, motion.move.grabbed, motion.mover, onOpen)) event.preventDefault()
  }
  return (
    <div className="fa-kanban__columns" aria-label={t('board')} role="group">
      {motion.columns.map((view) => (
        <KanbanColumn
          key={view.column.id}
          view={view}
          doneColumnId={doneColumn(board).id}
          today={today}
          canCreate={can.create}
          canToggle={can.move}
          grabbedId={motion.move.grabbed}
          draggingId={motion.drag.active ? motion.drag.card?.id ?? null : null}
          instructionsId={instructionsId}
          locale={props.locale}
          onAdd={onAdd}
          onOpen={onOpen}
          onToggleDone={(card) => void binding.controller.actions.toggle(card)}
          onCardKeyDown={onCardKey}
          onCardPointerDown={(event, card) => motion.pointer.onPointerDown(event, card)}
        />
      ))}
    </div>
  )
}

function Ghost({ motion, today, locale }: { motion: Mover; today: string; locale?: Locale }) {
  const { drag } = motion
  if (!drag.active || !drag.card) return null
  const style = { left: `${drag.x - drag.offsetX}px`, top: `${drag.y - drag.offsetY}px`, width: `${drag.width}px` }
  return <KanbanCard className="fa-kanban-card--ghost" ariaHidden card={drag.card} today={today} locale={locale} style={style} />
}

function useBoardHandlers(props: FlowauditKanbanBoardProps, binding: BoardBinding, motion: Mover) {
  const { t } = useKanbanText(props.locale)
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const open = (card: Card): void => {
    if (motion.pointer.consumeClick()) return
    setSelectedId(card.id)
    props.onCardOpen?.(card)
  }
  const addCard = async (columnId: string): Promise<void> => {
    if (!binding.view.can.create) return
    const known = new Set(binding.state.board?.cards.map((card) => card.id))
    const result = await binding.controller.actions.addCard(columnId, { title: t('newCardTitle') })
    const created = result?.board.cards.find((card) => !known.has(card.id))
    if (created) setSelectedId(created.id)
  }
  const selected = binding.state.board && selectedId ? findCard(binding.state.board, selectedId) ?? null : null
  return { selectedId, setSelectedId, selected, open, addCard }
}

export const FlowauditKanbanBoard = forwardRef<FlowauditKanbanBoardHandle, FlowauditKanbanBoardProps>(function FlowauditKanbanBoard(props, ref) {
  const { t } = useKanbanText(props.locale)
  const root = useRef<HTMLDivElement | null>(null)
  const search = useRef<HTMLInputElement>(null)
  const instructionsId = useElementId('fa-kanban-help')
  const binding = useBoard(props)
  const motion = useMover(binding, t, root)
  const handlers = useBoardHandlers(props, binding, motion)
  const [dialog, setDialog] = useState<'settings' | 'share' | null>(null)
  const { state, view } = binding
  useImperativeHandle(ref, () => ({ reload: binding.controller.load, board: state.board }), [binding.controller, state.board])
  useBoardShortcuts(root, (shortcut) => {
    if (shortcut === 'fullscreen') props.onFullscreen?.()
    else if (shortcut === 'search') search.current?.focus()
    else if (state.board?.columns[0]) void handlers.addCard(state.board.columns[0].id)
  })
  const board = state.board
  return (
    <div ref={root} className="fa-kanban" aria-busy={state.loading || undefined}>
      <StatusLines props={props} binding={binding} announcement={motion.move.announcement} instructionsId={instructionsId} />
      {board ? (
        <>
          <KanbanToolbar
            title={board.title}
            stats={view.stats}
            filter={binding.filter}
            filterActive={binding.filterActive}
            canRename={view.can.rename}
            canShare={view.can.share}
            canConfigure={view.can.configure}
            showFullscreen={props.showFullscreen ?? true}
            locale={props.locale}
            searchRef={search}
            onRename={(title) => void binding.controller.actions.rename(title)}
            onShare={() => setDialog('share')}
            onSettings={() => setDialog('settings')}
            onFullscreen={props.onFullscreen}
            onResetFilter={() => binding.setFilter({ query: '', priority: '', due: '', tag: '' })}
            onFilterChange={(patch) => binding.setFilter((current) => ({ ...current, ...patch }))}
          />
          <Columns props={props} binding={binding} motion={motion} instructionsId={instructionsId} onAdd={(columnId) => void handlers.addCard(columnId)} onOpen={handlers.open} />
          <Ghost motion={motion} today={view.today} locale={props.locale} />
          <BoardDialogs props={props} binding={binding} board={board} selected={handlers.selected} dialog={dialog} setDialog={setDialog} onCloseCard={() => handlers.setSelectedId(null)} />
        </>
      ) : null}
    </div>
  )
})
