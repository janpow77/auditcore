import type { DragEvent, KeyboardEvent } from 'react'
import type { DbCardView, DbKanbanTranslate } from '@auditcore/ui-core'
import { classes } from '../store'

export interface DbKanbanCardProps {
  card: DbCardView
  columnLabel: string
  t: DbKanbanTranslate
  editable?: boolean
  dragging?: boolean
  describedBy?: string
  onCardDrag: (id: string | null) => void
  onCardStep: (id: string, direction: 1 | -1) => void
}

/** Karte der Datenbankansicht wie `DbKanbanCard.vue` (Ziehen, Strg+Pfeil). */
export function DbKanbanCard(props: DbKanbanCardProps) {
  const { card, editable = true } = props
  const onDragStart = (event: DragEvent<HTMLLIElement>): void => {
    event.dataTransfer?.setData('text/plain', card.id)
    if (event.dataTransfer) event.dataTransfer.effectAllowed = 'move'
    props.onCardDrag(card.id)
  }
  const onKeyDown = (event: KeyboardEvent<HTMLLIElement>): void => {
    if (!editable || !(event.ctrlKey || event.metaKey)) return
    if (event.key !== 'ArrowLeft' && event.key !== 'ArrowRight') return
    event.preventDefault()
    props.onCardStep(card.id, event.key === 'ArrowRight' ? 1 : -1)
  }
  return (
    <li
      className={classes('fa-db-kanban-card', props.dragging && 'fa-db-kanban-card--dragging')}
      data-card-id={card.id}
      tabIndex={0}
      draggable={editable ? 'true' : 'false'}
      aria-label={props.t('cardLabel', { title: card.title, label: props.columnLabel })}
      aria-describedby={editable ? props.describedBy : undefined}
      onDragStart={onDragStart}
      onDragEnd={() => props.onCardDrag(null)}
      onKeyDown={onKeyDown}
    >
      <p className="fa-db-kanban-card__title">{card.title}</p>
      {card.fields.length ? (
        <dl className="fa-db-kanban-card__fields">
          {card.fields.map((field) => (
            <div key={field.id} className="fa-db-kanban-card__field">
              <dt>{field.label}</dt>
              <dd>{field.text}</dd>
            </div>
          ))}
        </dl>
      ) : null}
    </li>
  )
}
