/** Search for elements by name, id, role or domain key; Enter jumps to the first hit. */

import { useMemo, useState, type KeyboardEvent } from 'react'
import { displayName, type ProcessModel } from '@flowaudit/bpmn-flowaudit'
import { searchElements } from '@flowaudit/bpmn-flowaudit/ui'
import { BaseDialog } from '../base/BaseDialog'
import { useI18n } from '../i18n'

export interface ElementSearchProps {
  open: boolean
  model: ProcessModel | null
  onOpenChange: (open: boolean) => void
  onJump: (id: string) => void
}

export function ElementSearch({ open, model, onOpenChange, onJump }: ElementSearchProps) {
  const { t } = useI18n()
  const [query, setQuery] = useState('')
  const hits = useMemo(() => searchElements(model, query), [model, query])

  const jump = (id: string) => {
    onJump(id)
    onOpenChange(false)
  }

  const onKeyDown = (event: KeyboardEvent) => {
    if (event.key !== 'Enter') return
    event.preventDefault()
    if (hits[0]) jump(hits[0].id)
  }

  return (
    <BaseDialog open={open} title={t('search.title')} width="520px" onOpenChange={onOpenChange}>
      <input className="fa-input" type="search" placeholder={t('search.placeholder')} aria-label={t('search.title')} value={query} onChange={(event) => setQuery(event.target.value)} onKeyDown={onKeyDown} />
      <ul className="fa-search__hits" role="listbox">
        {hits.map((hit) => (
          <li key={hit.id}>
            <button type="button" role="option" className="fa-menu-item" onClick={() => jump(hit.id)}>
              <span>
                <strong>{displayName(hit)}</strong>
                <span className="fa-menu-hint">{hit.type.replace('bpmn:', '')} · {hit.id}</span>
              </span>
            </button>
          </li>
        ))}
      </ul>
      {query.trim() && !hits.length ? <p className="fa-help">{t('search.none')}</p> : null}
    </BaseDialog>
  )
}
