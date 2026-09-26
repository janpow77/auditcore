/**
 * Import enrichment: suggestions from documentation, labels and colours,
 * grouped by element; each can be accepted or rejected.
 */

import { useEffect, useMemo, useState } from 'react'
import type { Suggestion } from '@flowaudit/bpmn-flowaudit'
import { describeSuggestion, groupSuggestions, toggleInSet } from '@flowaudit/bpmn-flowaudit/ui'
import { BaseDialog } from '../base/BaseDialog'
import { useI18n } from '../i18n'

export interface EnrichmentDialogProps {
  open: boolean
  suggestions: Suggestion[]
  names: Record<string, string>
  onOpenChange: (open: boolean) => void
  onApply: (accepted: Suggestion[], removePrefixes: boolean) => void
}

function SuggestionItem({ item, checked, onToggle }: { item: Suggestion; checked: boolean; onToggle: () => void }) {
  const { t } = useI18n()
  return (
    <li>
      <label className="fa-enrich__item">
        <input type="checkbox" checked={checked} onChange={onToggle} />
        <span className="fa-badge fa-badge--info">{t(`enrich.kind.${item.kind}`)}</span>
        <span className="fa-enrich__value">{describeSuggestion(item)}</span>
        <span className="fa-help">{t(`enrich.origin.${item.origin}`)}: „{item.excerpt}“</span>
      </label>
    </li>
  )
}

export function EnrichmentDialog({ open, suggestions, names, onOpenChange, onApply }: EnrichmentDialogProps) {
  const { t } = useI18n()
  const [accepted, setAccepted] = useState(() => new Set(suggestions.map((s) => s.id)))
  const [removePrefixes, setRemovePrefixes] = useState(true)
  const groups = useMemo(() => groupSuggestions(suggestions), [suggestions])

  useEffect(() => {
    if (open) setAccepted(new Set(suggestions.map((s) => s.id)))
  }, [open, suggestions])

  const apply = () => {
    onApply(suggestions.filter((s) => accepted.has(s.id)), removePrefixes)
    onOpenChange(false)
  }

  const footer = (
    <>
      <button type="button" className="fa-btn" onClick={() => onOpenChange(false)}>{t('common.cancel')}</button>
      <button type="button" className="fa-btn fa-btn--primary" disabled={!accepted.size} onClick={apply}>{t('enrich.apply', { count: accepted.size })}</button>
    </>
  )

  return (
    <BaseDialog open={open} title={t('enrich.title')} subtitle={t('enrich.subtitle')} width="820px" onOpenChange={onOpenChange} footer={footer}>
      {!suggestions.length ? (
        <p className="fa-help">{t('enrich.none')}</p>
      ) : (
        <div className="fa-enrich__bar">
          <button type="button" className="fa-btn fa-btn--ghost" onClick={() => setAccepted(new Set(suggestions.map((s) => s.id)))}>{t('enrich.selectAll')}</button>
          <button type="button" className="fa-btn fa-btn--ghost" onClick={() => setAccepted(new Set())}>{t('enrich.selectNone')}</button>
          <label className="fa-check"><input type="checkbox" checked={removePrefixes} onChange={(event) => setRemovePrefixes(event.target.checked)} />{t('enrich.removePrefixes')}</label>
        </div>
      )}
      {groups.map(([elementId, items]) => (
        <section key={elementId} className="fa-enrich__group">
          <h3 className="fa-section__title">{names[elementId] || elementId}</h3>
          <ul className="fa-enrich__list">
            {items.map((item) => <SuggestionItem key={item.id} item={item} checked={accepted.has(item.id)} onToggle={() => setAccepted((current) => toggleInSet(current, item.id))} />)}
          </ul>
        </section>
      ))}
    </BaseDialog>
  )
}
