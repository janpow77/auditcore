import { intlFormatDate } from '@auditcore/common'
import { badgeStyle, cardAge, cardStyle, deadlineState, preview, PRIORITY_TONES, type Card } from '@auditcore/kanban-core'
import type { Locale } from '@auditcore/ui-core'
import type { CSSProperties, KeyboardEvent, MouseEvent, PointerEvent } from 'react'
import { Icon } from '../base/Icon'
import { classes } from '../store'
import { useKanbanText } from './text'

export interface KanbanCardProps {
  card: Card
  done?: boolean
  today: string
  now?: number
  canToggle?: boolean
  grabbed?: boolean
  dragging?: boolean
  describedBy?: string
  locale?: Locale
  /** Schwebendes Abbild beim Ziehen (Klasse, Stil, aria-hidden wie in Vue). */
  className?: string
  style?: CSSProperties
  ariaHidden?: boolean
  onOpen?: (card: Card) => void
  onToggleDone?: (card: Card) => void
  onKeyDown?: (event: KeyboardEvent<HTMLElement>, card: Card) => void
  onPointerDown?: (event: PointerEvent<HTMLElement>, card: Card) => void
}

type Text = ReturnType<typeof useKanbanText>

function formatDue(due: string, locale: Locale): string {
  return intlFormatDate(due, locale)
}

function CardHead({ props, t }: { props: KanbanCardProps; t: Text['t'] }) {
  const { card, done = false } = props
  const toggle = (event: MouseEvent<HTMLButtonElement>): void => {
    event.stopPropagation()
    props.onToggleDone?.(card)
  }
  return (
    <div className="fa-kanban-card__head">
      {props.canToggle ? (
        <button type="button" className="fa-kanban-card__check" aria-label={done ? t('markOpen') : t('markDone')} aria-pressed={done} onClick={toggle}>
          {done ? <Icon name="check" size={12} /> : null}
        </button>
      ) : null}
      {card.badge ? <span className="fa-kanban-card__badge" style={badgeStyle(card.badge)}>{card.badge}</span> : null}
      <h3 className="fa-kanban-card__title">{card.title}</h3>
      <Icon name="grip" className="fa-kanban-card__grip" size={16} />
    </div>
  )
}

function CardChips({ card, t }: { card: Card; t: Text['t'] }) {
  const checklistDone = card.checklist.filter((item) => item.done).length
  if (!card.tags.length && !card.checklist.length) return null
  return (
    <div className="fa-kanban-card__chips">
      {card.tags.slice(0, 3).map((tag) => <span key={tag} className="fa-kanban-card__tag">{tag}</span>)}
      {card.tags.length > 3 ? <span className="fa-kanban-card__tag">{t('moreTags', { count: card.tags.length - 3 })}</span> : null}
      {card.checklist.length ? (
        <span className={classes('fa-kanban-card__tag', checklistDone === card.checklist.length && 'is-complete')}>
          <Icon name="check" size={11} /> {checklistDone}/{card.checklist.length}
        </span>
      ) : null}
    </div>
  )
}

function CardMeta({ props, text }: { props: KanbanCardProps; text: Text }) {
  const { card } = props
  const { t, locale } = text
  const due = deadlineState(card.due, props.today)
  const age = cardAge(card.created_at, props.now ?? Date.now())
  return (
    <div className="fa-kanban-card__meta">
      <span className={`fa-kanban-card__priority is-${PRIORITY_TONES[card.priority]}`}>{t(`priority_${card.priority}`)}</span>
      {card.due ? (
        <span className={`fa-kanban-card__due is-${due}`} title={t('dueOn', { date: formatDue(card.due, locale) })}>
          <Icon name="clock" size={12} /> {formatDue(card.due, locale)}
        </span>
      ) : null}
      {card.attachments.length ? <span title={t('attachments', { count: card.attachments.length })}><Icon name="paperclip" size={12} /> {card.attachments.length}</span> : null}
      {card.links.length ? <span title={t('links', { count: card.links.length })}><Icon name="share" size={12} /> {card.links.length}</span> : null}
      {card.assignees.length ? <span className="fa-kanban-card__people"><Icon name="user" size={12} /> {card.assignees.length}</span> : null}
      {age ? <span className="fa-kanban-card__age">{t(age.key, { count: age.count })}</span> : null}
    </div>
  )
}

function cardLabel(card: Card, today: string, t: Text['t']): string {
  const due = card.due ? t(`due_${deadlineState(card.due, today)}`) : ''
  return [card.badge, card.title, t(`priority_${card.priority}`), due].filter(Boolean).join(', ')
}

function cardClass({ card, done, grabbed, dragging, className }: KanbanCardProps): string {
  return classes(
    'fa-kanban-card', `fa-kanban-card--${card.priority}`, done && 'fa-kanban-card--done', Boolean(card.color || card.image) && 'fa-kanban-card--styled',
    grabbed && 'fa-kanban-card--grabbed', dragging && 'fa-kanban-card--dragging', className,
  )
}

/** Karte wie `KanbanCard.vue` (gleiches Markup, Tastatur und Zeiger über das Board). */
export function KanbanCard(props: KanbanCardProps) {
  const text = useKanbanText(props.locale)
  const { card, done = false } = props
  return (
    <article
      className={cardClass(props)}
      style={{ ...cardStyle(card.color, card.image), ...props.style }}
      data-card-id={card.id}
      tabIndex={0}
      role="listitem"
      aria-roledescription={text.t('cardRole')}
      aria-label={cardLabel(card, props.today, text.t)}
      aria-describedby={props.describedBy}
      aria-pressed={props.grabbed ? 'true' : undefined}
      aria-hidden={props.ariaHidden ? 'true' : undefined}
      onClick={() => props.onOpen?.(card)}
      onKeyDown={(event) => props.onKeyDown?.(event, card)}
      onPointerDown={(event) => props.onPointerDown?.(event, card)}
    >
      <CardHead props={props} t={text.t} />
      {card.description && !done ? <p className="fa-kanban-card__text">{preview(card.description)}</p> : null}
      {done ? null : <CardChips card={card} t={text.t} />}
      <CardMeta props={props} text={text} />
    </article>
  )
}
