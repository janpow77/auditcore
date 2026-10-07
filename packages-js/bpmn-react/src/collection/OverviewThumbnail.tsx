/**
 * Thumbnail of one diagram in the folder overview: requested only once it
 * scrolls into view, shown as an image (never as inline SVG), a quiet
 * placeholder while loading or without a picture – React counterpart of the
 * Vue `OverviewThumbnail`.
 */

import { useEffect, useRef, useState } from 'react'
import type { Thumbnails } from '@auditcore/bpmn-flowaudit/ui'
import { useI18n } from '../i18n'

export interface OverviewThumbnailProps {
  diagramId: string
  name: string
  thumbnails: Thumbnails
}

type LoadState = 'waiting' | 'loading' | 'done'

export function OverviewThumbnail({ diagramId, name, thumbnails }: OverviewThumbnailProps) {
  const { t } = useI18n()
  const root = useRef<HTMLDivElement | null>(null)
  const [url, setUrl] = useState<string | null>(null)
  const [state, setState] = useState<LoadState>('waiting')

  useEffect(() => {
    let alive = true
    const load = () => {
      setState('loading')
      void thumbnails.get(diagramId).then((value) => alive && (setUrl(value), setState('done')))
    }
    if (typeof IntersectionObserver === 'undefined' || !root.current) {
      load()
      return () => void (alive = false)
    }
    const observer = new IntersectionObserver((entries) => entries.some((entry) => entry.isIntersecting) && (observer.disconnect(), load()), { rootMargin: '200px' })
    observer.observe(root.current)
    return () => {
      alive = false
      observer.disconnect()
    }
  }, [diagramId, thumbnails])

  return (
    <div ref={root} className={`fa-thumb__image${state === 'loading' ? ' fa-thumb__image--loading' : ''}`}>
      {url ? <img src={url} alt={t('collection.overview.thumbnail', { name })} loading="lazy" decoding="async" /> : null}
      {!url && state === 'done' ? <span className="fa-thumb__empty">{t('collection.overview.noThumbnail')}</span> : null}
    </div>
  )
}
