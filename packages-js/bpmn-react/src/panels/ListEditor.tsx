/**
 * Editable list of FlowAudit entries (controls, risks, findings, …) from a
 * declarative `ListDescriptor`: collapsible items, add and remove.
 */

import { useState } from 'react'
import { removeAt, replaceAt, toggleIndex, type FieldDescriptor, type ListDescriptor, type Option } from '@auditcore/bpmn-flowaudit/ui'
import { FaIcon } from '../base/FaIcon'
import { classes } from '../hooks'
import { useI18n } from '../i18n'
import { FieldForm } from './FieldForm'

type Row = Record<string, unknown>

export interface ListEditorProps {
  descriptor: ListDescriptor
  items: Row[]
  optionsFor: (field: FieldDescriptor) => Option[]
  disabled?: boolean
  className?: string
  onUpdate: (items: Row[]) => void
}

export function ListEditor({ descriptor, items, optionsFor, disabled, className, onUpdate }: ListEditorProps) {
  const { t } = useI18n()
  const [open, setOpen] = useState<number | null>(null)

  const add = () => {
    onUpdate([...items, descriptor.create()])
    setOpen(items.length)
  }

  const remove = (index: number) => {
    onUpdate(removeAt(items, index))
    setOpen(null)
  }

  return (
    <section className={classes('fa-list-editor', className)}>
      <header className="fa-list-editor__head">
        <h3>
          {t(descriptor.title)} <span className="fa-badge">{items.length}</span>
        </h3>
        <button type="button" className="fa-btn fa-btn--ghost" disabled={disabled} onClick={add}>
          <FaIcon name="plus" size={16} />
          {t('common.add')}
        </button>
      </header>
      {!items.length ? <p className="fa-help">{t('common.empty')}</p> : null}
      <ul className="fa-list-editor__items">
        {items.map((item, index) => (
          <li key={index} className="fa-card">
            <div className="fa-list-editor__row">
              <button type="button" className="fa-list-editor__toggle" aria-expanded={open === index} onClick={() => setOpen(toggleIndex(open, index))}>
                <FaIcon name={open === index ? 'chevron-down' : 'chevron-right'} size={16} />
                <span className="fa-list-editor__summary">{descriptor.summary(item) || t('common.new')}</span>
                {(descriptor.badges?.(item) ?? []).map((badge) => (
                  <span key={badge} className="fa-badge fa-badge--info">{t(badge)}</span>
                ))}
              </button>
              <button type="button" className="fa-icon-btn" disabled={disabled} aria-label={t('common.remove')} onClick={() => remove(index)}>
                <FaIcon name="delete" size={16} />
              </button>
            </div>
            {open === index ? (
              <div className="fa-list-editor__form">
                <FieldForm value={item} fields={descriptor.fields} optionsFor={optionsFor} disabled={disabled} onUpdate={(value) => onUpdate(replaceAt(items, index, value))} />
              </div>
            ) : null}
          </li>
        ))}
      </ul>
    </section>
  )
}
