/**
 * Key filter „all elements for key X“ (KA, BK, checklist item, finding
 * reference, register, role, marker). Values come from the diagram's own
 * key index; the application can also set a key through `FlowauditEditor`.
 */

import { useMemo } from 'react'
import { KEY_KINDS, type KeyKind } from '@auditcore/bpmn-flowaudit'
import { FaIcon } from '../base/FaIcon'
import { useI18n } from '../i18n'

export interface KeyFilterBarProps {
  keys: Partial<Record<KeyKind, Record<string, string[]>>>
  kind: KeyKind
  value: string
  hits: number
  onKindChange: (kind: KeyKind) => void
  onValueChange: (value: string) => void
  onClear: () => void
}

export function KeyFilterBar({ keys, kind, value, hits, onKindChange, onValueChange, onClear }: KeyFilterBarProps) {
  const { t } = useI18n()
  const values = useMemo(() => Object.keys(keys[kind] ?? {}).sort((a, b) => a.localeCompare(b, 'de', { numeric: true })), [keys, kind])
  return (
    <div className="fa-keyfilter" role="search" aria-label={t('filter.title')}>
      <FaIcon name="filter" />
      <label className="fa-keyfilter__field">
        <span className="fa-sr-only">{t('filter.kind')}</span>
        <select className="fa-select" value={kind} onChange={(event) => onKindChange(event.target.value as KeyKind)}>
          {KEY_KINDS.map((option) => <option key={option} value={option}>{t(`filter.kind.${option}`)}</option>)}
        </select>
      </label>
      <label className="fa-keyfilter__field">
        <span className="fa-sr-only">{t('filter.value')}</span>
        <input className="fa-input" list="fa-keyfilter-values" value={value} placeholder={t('filter.value')} onChange={(event) => onValueChange(event.target.value)} />
        <datalist id="fa-keyfilter-values">
          {values.map((option) => <option key={option} value={option} />)}
        </datalist>
      </label>
      <span className={hits ? 'fa-badge fa-badge--info' : 'fa-badge'} role="status">{t('filter.hits', { count: hits })}</span>
      <button type="button" className="fa-btn fa-btn--ghost" onClick={onClear}><FaIcon name="close" size={16} />{t('filter.clear')}</button>
    </div>
  )
}
