import { DUE_STATES, PRIORITIES, type BoardStats, type KanbanFilterState } from '@auditcore/kanban-core'
import type { Locale } from '@auditcore/ui-core'
import { useLayoutEffect, useRef, useState, type KeyboardEvent, type Ref } from 'react'
import { Button } from '../base/Button'
import { TextField } from '../base/TextField'
import { useKanbanText } from './text'

export interface KanbanToolbarProps {
  title: string
  stats: BoardStats | null
  filter: KanbanFilterState
  filterActive?: boolean
  canRename?: boolean
  canShare?: boolean
  canConfigure?: boolean
  showFullscreen?: boolean
  locale?: Locale
  /** Suchfeld (Tastenkürzel „/“ fokussiert es). */
  searchRef?: Ref<HTMLInputElement>
  onRename?: (title: string) => void
  onShare?: () => void
  onSettings?: () => void
  onFullscreen?: () => void
  onResetFilter?: () => void
  onFilterChange?: (patch: Partial<KanbanFilterState>) => void
}

function TitleEditor({ props }: { props: KanbanToolbarProps }) {
  const { t } = useKanbanText(props.locale)
  const [draft, setDraft] = useState<string | null>(null)
  const input = useRef<HTMLInputElement | null>(null)
  const editing = draft !== null
  useLayoutEffect(() => {
    if (editing) input.current?.select()
  }, [editing])
  const commit = (): void => {
    if (draft === null) return
    setDraft(null)
    const value = draft.trim()
    if (value && value !== props.title) props.onRename?.(value)
  }
  const onKeyDown = (event: KeyboardEvent<HTMLInputElement>): void => {
    if (event.key === 'Enter') { event.preventDefault(); commit() }
    else if (event.key === 'Escape') { event.preventDefault(); setDraft(null) }
  }
  if (editing) {
    return <input ref={input} className="fa-kanban-toolbar__title-input" aria-label={t('renameLabel')} value={draft} onChange={(event) => setDraft(event.target.value)} onBlur={commit} onKeyDown={onKeyDown} />
  }
  return (
    <h1 className="fa-kanban-toolbar__heading">
      {props.canRename ? <button type="button" className="fa-kanban-toolbar__rename" title={t('renameHint')} onClick={() => setDraft(props.title)}>{props.title}</button> : props.title}
    </h1>
  )
}

function Progress({ stats, locale }: { stats: BoardStats; locale?: Locale }) {
  const { t } = useKanbanText(locale)
  const label = t('progress', { done: stats.done, total: stats.total })
  return (
    <div className="fa-kanban-toolbar__progress">
      <span>{label}</span>
      <span className="fa-kanban-toolbar__bar" role="progressbar" aria-valuenow={stats.progress} aria-valuemin={0} aria-valuemax={100} aria-label={label}>
        <span style={{ width: `${stats.progress}%` }} />
      </span>
      <span>{stats.progress} %</span>
    </div>
  )
}

function FilterTools({ props }: { props: KanbanToolbarProps }) {
  const { t } = useKanbanText(props.locale)
  const change = (patch: Partial<KanbanFilterState>): void => props.onFilterChange?.(patch)
  return (
    <>
      <TextField inputRef={props.searchRef} value={props.filter.query} className="fa-kanban-toolbar__search" type="search" label={t('search')} placeholder={t('searchPlaceholder')} hideLabel onChange={(query) => change({ query })} />
      <select value={props.filter.priority} className="fa-kanban-select" aria-label={t('priorityFilter')} onChange={(event) => change({ priority: event.target.value as KanbanFilterState['priority'] })}>
        <option value="">{t('allPriorities')}</option>
        {PRIORITIES.map((priority) => <option key={priority} value={priority}>{t(`priority_${priority}`)}</option>)}
      </select>
      <select value={props.filter.due} className="fa-kanban-select" aria-label={t('dueFilter')} onChange={(event) => change({ due: event.target.value as KanbanFilterState['due'] })}>
        <option value="">{t('allDue')}</option>
        {DUE_STATES.map((state) => <option key={state} value={state}>{t(`due_${state}`)}</option>)}
      </select>
    </>
  )
}

/** Werkzeugleiste wie `KanbanToolbar.vue` (Titel, Fortschritt, Suche, Filter, Aktionen). */
export function KanbanToolbar(props: KanbanToolbarProps) {
  const { t } = useKanbanText(props.locale)
  return (
    <div className="fa-kanban-toolbar">
      <div className="fa-kanban-toolbar__title">
        <TitleEditor props={props} />
        {props.stats ? <Progress stats={props.stats} locale={props.locale} /> : null}
      </div>
      <div className="fa-kanban-toolbar__tools">
        <FilterTools props={props} />
        {props.filterActive ? <Button size="sm" variant="ghost" icon="close" onClick={props.onResetFilter}>{t('resetFilter')}</Button> : null}
        {props.showFullscreen ?? true ? <Button variant="ghost" icon="expand" iconOnly label={t('fullscreen')} onClick={props.onFullscreen} /> : null}
        {props.canShare ? <Button variant="ghost" icon="share" iconOnly label={t('share')} onClick={props.onShare} /> : null}
        {props.canConfigure ? <Button variant="ghost" icon="settings" iconOnly label={t('settings')} onClick={props.onSettings} /> : null}
      </div>
    </div>
  )
}
