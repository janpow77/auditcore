import { intlFormatDate } from '@flowaudit/common'
import { PRIORITIES, type Attachment, type Card, type CardLink, type Column } from '@flowaudit/kanban-core'
import type { Locale } from '@flowaudit/ui-core'
import { useState, type ReactNode } from 'react'
import { Button } from '../base/Button'
import { Dialog } from '../base/Dialog'
import { CardAppearance } from './CardAppearance'
import { CardChecklistEditor } from './CardChecklistEditor'
import { CardReferences } from './CardReferences'
import { CardTagsEditor } from './CardTagsEditor'
import { CardFields, CardTexts, useCardDraft } from './CardFields'
import { useKanbanDialogText, useKanbanText } from './text'

export interface KanbanCardDetailProps {
  card: Card | null
  columns: readonly Column[]
  readOnly?: boolean
  canDelete?: boolean
  locale?: Locale
  /** Zusatzinhalt je Karte (Slot `extra` in Vue). */
  renderExtra?: (card: Card) => ReactNode
  onClose: () => void
  onUpdate?: (fields: Record<string, unknown>) => void
  onDelete?: (card: Card) => void
  onNavigate?: (link: CardLink) => void
  onAttachment?: (attachment: Attachment) => void
}

function PriorityPicker({ card, props }: { card: Card; props: KanbanCardDetailProps }) {
  const { t } = useKanbanDialogText(props.locale)
  const { t: tk } = useKanbanText(props.locale)
  return (
    <div className="fa-kanban-detail__section">
      <span id="fa-kanban-priority" className="fa-kanban-detail__label">{t('priority')}</span>
      <div className="fa-kanban-detail__row" role="radiogroup" aria-labelledby="fa-kanban-priority">
        {PRIORITIES.map((priority) => (
          <Button key={priority} size="sm" variant={card.priority === priority ? 'primary' : 'secondary'} role="radio" ariaChecked={card.priority === priority} disabled={props.readOnly} onClick={() => props.onUpdate?.({ priority })}>
            {tk(`priority_${priority}`)}
          </Button>
        ))}
      </div>
    </div>
  )
}

function DetailBody({ card, props, update }: { card: Card; props: KanbanCardDetailProps; update: (fields: Record<string, unknown>) => void }) {
  const { t, locale } = useKanbanDialogText(props.locale)
  const draft = useCardDraft(card)
  const readOnly = props.readOnly ?? false
  return (
    <div className="fa-kanban-detail">
      <CardTexts card={card} draft={draft} readOnly={readOnly} label={t} update={update} />
      <CardFields card={card} columns={props.columns} readOnly={readOnly} locale={props.locale} update={update} />
      <PriorityPicker card={card} props={{ ...props, onUpdate: update }} />
      <label className="fa-kanban-detail__section">
        <span className="fa-kanban-detail__label">{t('description')}</span>
        <textarea className="fa-kanban-detail__textarea" placeholder={t('descriptionPlaceholder')} readOnly={readOnly} value={draft.description} onChange={(event) => draft.setDescription(event.target.value)} onBlur={() => draft.description !== card.description && update({ description: draft.description })} />
      </label>
      <CardTagsEditor tags={card.tags} readOnly={readOnly} locale={props.locale} onChange={(tags) => update({ tags })} />
      <CardChecklistEditor items={card.checklist} readOnly={readOnly} locale={props.locale} onChange={(checklist) => update({ checklist })} />
      <CardAppearance color={card.color} image={card.image} readOnly={readOnly} locale={props.locale} onChange={update} />
      <CardReferences links={card.links} attachments={card.attachments} locale={props.locale} onNavigate={props.onNavigate} onAttachment={props.onAttachment} />
      {props.renderExtra?.(card)}
      <div className="fa-kanban-detail__meta">
        <p>{t('created', { date: intlFormatDate(card.created_at, locale, true) })}</p>
        <p>{t('updated', { date: intlFormatDate(card.updated_at, locale, true) })}</p>
      </div>
    </div>
  )
}

function useDetailActions(props: KanbanCardDetailProps) {
  const { card } = props
  const [confirming, setConfirming] = useState(false)
  if (!card && confirming) setConfirming(false)
  const update = (fields: Record<string, unknown>): void => {
    if (!props.readOnly) props.onUpdate?.(fields)
  }
  const remove = (): void => {
    if (!card) return
    if (confirming) props.onDelete?.(card)
    else setConfirming(true)
  }
  return { confirming, update, remove }
}

/** Detailansicht einer Karte wie `KanbanCardDetail.vue` (seitlicher Dialog). */
export function KanbanCardDetail(props: KanbanCardDetailProps) {
  const { t } = useKanbanDialogText(props.locale)
  const { card } = props
  const { confirming, update, remove } = useDetailActions(props)
  const deletable = Boolean(card && props.canDelete && !props.readOnly)
  const footer = deletable ? <Button variant={confirming ? 'danger' : 'secondary'} icon="trash" onClick={remove}>{confirming ? t('confirmDelete') : t('deleteCard')}</Button> : null
  return (
    <Dialog open={card !== null} title={card?.title || t('detailTitle')} placement="side" locale={props.locale} footer={footer} onClose={props.onClose}>
      {card ? <DetailBody card={card} props={props} update={update} /> : null}
    </Dialog>
  )
}
