/**
 * Search field for legal bases: parses the typed citation and asks the
 * legal search port (if present) for suggestions (debounced). Reports the
 * chosen entry through `onChoose`.
 */

import { useEffect, useState } from 'react'
import { shortCitation, type LegalBasis, type LegalSearchHit, type LegalSearchPort } from '@auditcore/bpmn-flowaudit'
import { hitHint, typedCitation, withoutDisplayFields } from '@auditcore/bpmn-flowaudit/ui'
import { FaIcon } from '../../base/FaIcon'
import { useElementId } from '../../hooks'
import { useI18n } from '../../i18n'

export interface LegalSearchProps {
  port?: LegalSearchPort
  profileId?: string
  disabled?: boolean
  onChoose: (value: LegalBasis) => void
}

function useHits(query: string, port: LegalSearchPort | undefined, profileId: string | undefined) {
  const { locale } = useI18n()
  const [hits, setHits] = useState<LegalSearchHit[]>([])
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    const controller = new AbortController()
    const timer = setTimeout(async () => {
      if (!port || query.trim().length < 2) return setHits([])
      setBusy(true)
      try {
        const found = await port.search(query, { locale, limit: 12, profile: profileId, signal: controller.signal })
        if (!controller.signal.aborted) setHits(found)
      } catch {
        if (!controller.signal.aborted) setHits([])
      } finally {
        if (!controller.signal.aborted) setBusy(false)
      }
    }, 250)
    return () => {
      clearTimeout(timer)
      controller.abort()
    }
  }, [query, port, profileId, locale])

  return { hits, busy, clear: () => setHits([]) }
}

export function LegalSearch({ port, profileId, disabled, onChoose }: LegalSearchProps) {
  const { t } = useI18n()
  const [query, setQuery] = useState('')
  const { hits, busy, clear } = useHits(query, port, profileId)
  const listId = useElementId('fa-legal')
  const typed = typedCitation(query)
  const shown = Boolean(query.trim())

  const choose = (value: LegalBasis) => {
    onChoose(withoutDisplayFields(value))
    setQuery('')
    clear()
  }

  return (
    <div className="fa-legal-search">
      <label className="fa-field">
        <span className="fa-label">{t('legal.search')}</span>
        <span className="fa-legal-search__input">
          <FaIcon name="search" size={16} />
          <input className="fa-input" type="search" value={query} disabled={disabled} aria-controls={shown ? listId : undefined} onChange={(event) => setQuery(event.target.value)} onKeyDown={(event) => event.key === 'Enter' && (event.preventDefault(), typed && choose(typed))} />
        </span>
      </label>
      {shown ? (
        <div id={listId} className="fa-legal-search__results" role="listbox" aria-busy={busy}>
          {typed ? (
            <button type="button" role="option" className="fa-menu-item" onClick={() => choose(typed)}>
              <FaIcon name="plus" size={16} />
              <span>
                {t('legal.takeTyped')}: <strong>{shortCitation(typed) || typed.text}</strong>
              </span>
            </button>
          ) : null}
          {hits.map((hit, index) => (
            <button key={index} type="button" role="option" className="fa-menu-item" onClick={() => choose(hit)}>
              <FaIcon name="marker-rechtsgrundlage" size={16} />
              <span>
                <strong>{shortCitation(hit) || hit.text}</strong>
                <span className="fa-menu-hint">{hitHint(hit)}</span>
                {hit.excerpt ? <span className="fa-menu-hint">{hit.excerpt}</span> : null}
              </span>
            </button>
          ))}
          {!busy && !hits.length && port ? <p className="fa-help">{t('legal.noResults')}</p> : null}
        </div>
      ) : null}
    </div>
  )
}
