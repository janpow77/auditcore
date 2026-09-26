import type { DragEvent } from 'react'
import type { DbColumnView, DbKanbanTranslate } from '@flowaudit/ui-core'
import { Button } from '../base/Button'
import { classes, useElementId } from '../store'
import { DbKanbanCard } from './DbKanbanCard'

export interface DbKanbanColumnProps {
  column: DbColumnView
  t: DbKanbanTranslate
  editable?: boolean
  canAdd?: boolean
  dragging?: string | null
  over?: boolean
  hintId?: string
  onCardDrag: (id: string | null) => void
  onCardStep: (id: string, direction: 1 | -1) => void
  onCardDrop: (id: string, column: string) => void
  onColumnOver: (column: string | null) => void
  onCardAdd: (column: string) => void
}

/** Spalte der Datenbankansicht wie `DbKanbanColumn.vue` (Ablegen setzt den Wert). */
export function DbKanbanColumn(props: DbKanbanColumnProps) {
  const { column, t, editable = true, dragging = null } = props
  const headingId = useElementId('fa-db-kanban-column')
  const onDragOver = (event: DragEvent<HTMLElement>): void => {
    if (!editable) return
    event.preventDefault()
    if (!props.over) props.onColumnOver(column.value)
  }
  const onDrop = (event: DragEvent<HTMLElement>): void => {
    if (!editable) return
    event.preventDefault()
    const id = event.dataTransfer?.getData('text/plain') || dragging
    if (id) props.onCardDrop(id, column.value)
  }
  const onDragLeave = (event: DragEvent<HTMLElement>): void => {
    if (event.target === event.currentTarget) props.onColumnOver(null)
  }
  return (
    <section
      className={classes('fa-db-kanban-column', props.over && 'fa-db-kanban-column--over', column.value === '' && 'fa-db-kanban-column--empty-value')}
      aria-labelledby={headingId} data-column={column.value} onDragOver={onDragOver} onDragLeave={onDragLeave} onDrop={onDrop}
    >
      <header className="fa-db-kanban-column__head">
        <h3 id={headingId} className="fa-db-kanban-column__name">{column.label}</h3>
        <span className="fa-db-kanban-column__count">{column.countText}</span>
      </header>
      <ul className="fa-db-kanban-column__list" aria-labelledby={headingId}>
        {column.cards.map((card) => (
          <DbKanbanCard key={card.id} card={card} columnLabel={column.label} t={t} editable={editable} dragging={dragging === card.id} describedBy={props.hintId} onCardDrag={props.onCardDrag} onCardStep={props.onCardStep} />
        ))}
      </ul>
      {column.cards.length === 0 ? <p className="fa-db-kanban-column__empty">{t('columnEmpty')}</p> : null}
      {editable && props.canAdd ? (
        <Button className="fa-db-kanban-column__add" size="sm" variant="ghost" icon="plus" ariaLabel={t('addCardIn', { label: column.label })} onClick={() => props.onCardAdd(column.value)}>{t('addCard')}</Button>
      ) : null}
    </section>
  )
}
