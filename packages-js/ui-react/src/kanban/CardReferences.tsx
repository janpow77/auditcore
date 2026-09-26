import { intlFormatNumber } from '@flowaudit/common'
import { fileSize, type Attachment, type CardLink } from '@flowaudit/kanban-core'
import type { Locale } from '@flowaudit/ui-core'
import type { ReactNode } from 'react'
import { Icon } from '../base/Icon'
import { useKanbanDialogText } from './text'

export interface CardReferencesProps {
  links: readonly CardLink[]
  attachments: readonly Attachment[]
  locale?: Locale
  /** Zusätzlicher Inhalt unter den Anhängen (Slot `attachments` in Vue). */
  attachmentsExtra?: ReactNode
  onNavigate?: (link: CardLink) => void
  onAttachment?: (attachment: Attachment) => void
}

function sizeText(bytes: number, locale: Locale): string {
  const { value, unit } = fileSize(bytes)
  return unit === 'B' ? `${value} B` : `${intlFormatNumber(value, locale, { maximumFractionDigits: 1 })} ${unit}`
}

/** Verknüpfungen und Anhänge einer Karte wie `CardReferences.vue`. */
export function CardReferences(props: CardReferencesProps) {
  const { t, locale } = useKanbanDialogText(props.locale)
  return (
    <>
      {props.links.length ? (
        <div className="fa-kanban-detail__section">
          <span className="fa-kanban-detail__label">{t('links')}</span>
          <ul className="fa-kanban-detail__list">
            {props.links.map((link) => (
              <li key={`${link.kind}:${link.target}`} className="fa-kanban-detail__item">
                <Icon name="share" size={14} />
                <button type="button" className="fa-kanban-toolbar__rename" aria-label={t('openLink', { title: link.title || link.target })} onClick={() => props.onNavigate?.(link)}>
                  {link.title || link.target}
                </button>
                <span className="fa-badge">{link.kind}</span>
              </li>
            ))}
          </ul>
        </div>
      ) : null}
      <div className="fa-kanban-detail__section">
        <span className="fa-kanban-detail__label">{t('attachments')}</span>
        {props.attachments.length ? (
          <ul className="fa-kanban-detail__list">
            {props.attachments.map((file) => (
              <li key={file.id} className="fa-kanban-detail__item">
                <Icon name="paperclip" size={14} />
                <button type="button" className="fa-kanban-toolbar__rename" onClick={() => props.onAttachment?.(file)}>{file.filename}</button>
                <span className="fa-kanban-detail__meta-inline">{sizeText(file.size, locale)}</span>
              </li>
            ))}
          </ul>
        ) : <p className="fa-kanban-settings__hint">{t('noAttachments')}</p>}
        {props.attachmentsExtra}
      </div>
    </>
  )
}
