/**
 * Structured recording of legal bases with search suggestions. 1.0 free text
 * entries stay visible as legacy and can be split into structured entries.
 */

import { useState } from 'react'
import { citation, isStructured, shortCitation, splitFreeText, type LegalBasis, type LegalSearchPort } from '@flowaudit/bpmn-flowaudit'
import { addLegalBasis, LEGAL_FIELDS, removeLegalBasis, structureLegalBasis, toggleIndex, updateLegalBasis } from '@flowaudit/bpmn-flowaudit/ui'
import { FaIcon } from '../../base/FaIcon'
import { useI18n } from '../../i18n'
import { FieldForm } from '../FieldForm'
import { LegalSearch } from './LegalSearch'

export interface LegalBasisEditorProps {
  items: LegalBasis[]
  port?: LegalSearchPort
  profileId?: string
  disabled?: boolean
  onUpdate: (items: LegalBasis[]) => void
}

const noOptions = () => []

function LegacyForm({ item, disabled, onStructure }: { item: LegalBasis; disabled?: boolean; onStructure: () => void }) {
  const { t } = useI18n()
  return (
    <>
      <p className="fa-help">{t('legal.legacyHelp')}</p>
      <ul className="fa-legal__legacy">
        {splitFreeText(item.text ?? '').map((part) => (
          <li key={part}>{part}</li>
        ))}
      </ul>
      <button type="button" className="fa-btn" disabled={disabled} onClick={onStructure}>
        <FaIcon name="enrich" size={16} />
        {t('legal.structure')}
      </button>
    </>
  )
}

function Summary({ item }: { item: LegalBasis }) {
  const { t } = useI18n()
  return (
    <span className="fa-legal__text">
      <strong>{shortCitation(item) || item.text}</strong>
      {isStructured(item) ? (
        <span className="fa-menu-hint">
          {t('legal.long')}: {citation(item)}
        </span>
      ) : (
        <span className="fa-badge fa-badge--warning">{t('legal.legacy')}</span>
      )}
    </span>
  )
}

export function LegalBasisEditor({ items, port, profileId, disabled, onUpdate }: LegalBasisEditorProps) {
  const { t } = useI18n()
  const [open, setOpen] = useState<number | null>(null)

  const add = (value: LegalBasis) => {
    const next = addLegalBasis(items, value)
    if (!next) return
    onUpdate(next)
    setOpen(null)
  }

  const structure = (index: number) => {
    const next = structureLegalBasis(items, index)
    if (next) onUpdate(next)
  }

  return (
    <section className="fa-legal">
      <LegalSearch port={port} profileId={profileId} disabled={disabled} onChoose={add} />
      {!items.length ? <p className="fa-help">{t('legal.empty')}</p> : null}
      <ul className="fa-list-editor__items fa-legal__items">
        {items.map((item, index) => (
          <li key={index} className="fa-card">
            <div className="fa-list-editor__row">
              <button type="button" className="fa-list-editor__toggle" aria-expanded={open === index} onClick={() => setOpen(toggleIndex(open, index))}>
                <FaIcon name={open === index ? 'chevron-down' : 'chevron-right'} size={16} />
                <Summary item={item} />
              </button>
              <button type="button" className="fa-icon-btn" disabled={disabled} aria-label={t('common.remove')} onClick={() => onUpdate(removeLegalBasis(items, index))}>
                <FaIcon name="delete" size={16} />
              </button>
            </div>
            {open === index ? (
              <div className="fa-list-editor__form">
                {isStructured(item) ? (
                  <FieldForm value={item as unknown as Record<string, unknown>} fields={LEGAL_FIELDS} optionsFor={noOptions} disabled={disabled} onUpdate={(value) => onUpdate(updateLegalBasis(items, index, value as LegalBasis))} />
                ) : (
                  <LegacyForm item={item} disabled={disabled} onStructure={() => structure(index)} />
                )}
              </div>
            ) : null}
          </li>
        ))}
      </ul>
    </section>
  )
}
