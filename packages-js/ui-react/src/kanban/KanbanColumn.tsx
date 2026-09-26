import type { Card, ColumnView } from '@auditcore/kanban-core'
import type { Locale } from '@auditcore/ui-core'
import type { CSSProperties, KeyboardEvent, PointerEvent } from 'react'
import { Button } from '../base/Button'
import { classes } from '../store'
import { KanbanCard } from './KanbanCard'
import { useKanbanText } from './text'

export interface KanbanColumnProps {
  view: ColumnView
  doneColumnId: string
  today: string
  canCreate?: boolean
  canToggle?: boolean
  grabbedId?: string | null
  draggingId?: string | null
  instructionsId?: string
  locale?: Locale
  onAdd?: (columnId: string) => void
  onOpen?: (card: Card) => void
  onToggleDone?: (card: Card) => void
  onCardKeyDown?: (event: KeyboardEvent<HTMLElement>, card: Card) => void
  onCardPointerDown?: (event: PointerEvent<HTMLElement>, card: Card) => void
}

function ColumnHead({ props, headingId }: { props: KanbanColumnProps; headingId: string }) {
  const { t } = useKanbanText(props.locale)
  const { view } = props
  const limit = view.wip?.limit ?? null
  const countLabel = limit === null ? t('cardCount', { count: view.total }) : t('wipLimit', { count: view.total, limit })
  return (
    <header className="fa-kanban-column__head">
      <h2 id={headingId} className="fa-kanban-column__name">
        <span className="fa-kanban-column__dot" aria-hidden="true" />
        {view.column.label}
      </h2>
      <span className={classes('fa-kanban-column__count', view.wip?.full && 'is-full', view.wip?.over && 'is-over')} title={countLabel} aria-label={countLabel}>
        {limit === null ? view.total : `${view.total}/${limit}`}
      </span>
      {props.canCreate ? (
        <Button size="sm" variant="ghost" icon="plus" iconOnly label={t('addCardIn', { column: view.column.label })} onClick={() => props.onAdd?.(view.column.id)} />
      ) : null}
    </header>
  )
}

/** Spalte wie `KanbanColumn.vue` (Kopf mit WIP-Anzeige, Kartenliste, Hinzufügen). */
export function KanbanColumn(props: KanbanColumnProps) {
  const { t } = useKanbanText(props.locale)
  const { view } = props
  const headingId = `fa-kanban-column-${view.column.id}`
  const style = { '--fa-kanban-column-color': view.column.color } as CSSProperties
  return (
    <section className={classes('fa-kanban-column', view.wip?.over && 'fa-kanban-column--over-limit')} style={style} data-column-id={view.column.id} aria-labelledby={headingId}>
      <ColumnHead props={props} headingId={headingId} />
      <div className="fa-kanban-column__list" role="list" aria-labelledby={headingId} data-card-list="">
        {view.cards.map((card) => (
          <KanbanCard
            key={card.id}
            card={card}
            done={card.column_id === props.doneColumnId}
            today={props.today}
            canToggle={props.canToggle}
            grabbed={props.grabbedId === card.id}
            dragging={props.draggingId === card.id}
            describedBy={props.instructionsId}
            locale={props.locale}
            onOpen={props.onOpen}
            onToggleDone={props.onToggleDone}
            onKeyDown={props.onCardKeyDown}
            onPointerDown={props.onCardPointerDown}
          />
        ))}
        {view.cards.length === 0 ? <p className="fa-kanban-column__empty">{t('emptyColumn')}</p> : null}
      </div>
      {props.canCreate ? (
        <Button className="fa-kanban-column__add" size="sm" variant="ghost" icon="plus" onClick={() => props.onAdd?.(view.column.id)}>
          {t('addCard')}
        </Button>
      ) : null}
    </section>
  )
}
