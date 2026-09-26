import type { ChangeEvent } from 'react'
import {
  CHANGE_STATUSES,
  ROW_STATUSES,
  statusLabel,
  type ClientExportFormat,
  type ServerExportLink,
  type SynopsisLayout,
  type SynopsisTranslate,
} from '@flowaudit/ui-core'
import { Button } from '../base/Button'
import { TextField } from '../base/TextField'
import { useElementId } from '../store'

export interface SynopsisToolbarProps {
  layout: SynopsisLayout
  statuses: readonly string[]
  query: string
  onlySelected: boolean
  highlight: boolean
  editable: boolean
  position: string
  canPrev: boolean
  canNext: boolean
  serverExports: readonly ServerExportLink[]
  t: SynopsisTranslate
  onLayout: (layout: SynopsisLayout) => void
  onQuery: (query: string) => void
  onOnlySelected: (value: boolean) => void
  onHighlight: (value: boolean) => void
  onToggleStatus: (status: string, enabled: boolean) => void
  onAllChanges: () => void
  onNavigate: (direction: 1 | -1) => void
  onExport: (format: ClientExportFormat) => void
}

const EXPORTS: ReadonlyArray<[ClientExportFormat, 'exportHtml' | 'exportMarkdown' | 'exportPrint']> = [
  ['html', 'exportHtml'],
  ['markdown', 'exportMarkdown'],
  ['print', 'exportPrint'],
]

const checked = (event: ChangeEvent<HTMLInputElement>): boolean => event.target.checked

function TopRow(props: SynopsisToolbarProps) {
  const { t, layout } = props
  return (
    <div className="fa-synopsis-toolbar__row">
      <div className="fa-synopsis-toolbar__group" role="group" aria-label={t('layout')}>
        <Button size="sm" variant="ghost" pressed={layout === 'side-by-side'} onClick={() => props.onLayout('side-by-side')}>{t('layoutSideBySide')}</Button>
        <Button size="sm" variant="ghost" pressed={layout === 'inline'} onClick={() => props.onLayout('inline')}>{t('layoutInline')}</Button>
      </div>
      <div className="fa-synopsis-toolbar__search">
        <TextField value={props.query} onChange={props.onQuery} type="search" label={t('search')} hideLabel placeholder={t('search')} />
      </div>
      <div className="fa-synopsis-toolbar__nav" role="group" aria-label={t('keyboardHint')}>
        <Button size="sm" icon="chevron-up" disabled={!props.canPrev} ariaKeyshortcuts="P K" onClick={() => props.onNavigate(-1)}>{t('prevChange')}</Button>
        <Button size="sm" icon="chevron-down" disabled={!props.canNext} ariaKeyshortcuts="N J" onClick={() => props.onNavigate(1)}>{t('nextChange')}</Button>
        <span className="fa-synopsis-toolbar__position" role="status" aria-live="polite">{props.position}</span>
      </div>
    </div>
  )
}

function Filters(props: SynopsisToolbarProps) {
  const { t, statuses } = props
  const allChanges = statuses.length === CHANGE_STATUSES.length && CHANGE_STATUSES.every((status) => statuses.includes(status))
  return (
    <fieldset className="fa-synopsis-toolbar__filters">
      <legend>{t('filterLegend')}</legend>
      <label><input type="checkbox" checked={allChanges} onChange={(event) => checked(event) && props.onAllChanges()} /> {t('filterAll')}</label>
      {ROW_STATUSES.map((status) => (
        <label key={status}>
          <input type="checkbox" checked={statuses.includes(status)} onChange={(event) => props.onToggleStatus(status, checked(event))} /> {statusLabel(status, t)}
        </label>
      ))}
    </fieldset>
  )
}

function Exports({ t, serverExports, onExport }: SynopsisToolbarProps) {
  const id = useElementId('fa-synopsis-toolbar')
  return (
    <div className="fa-synopsis-toolbar__export" role="group" aria-labelledby={`${id}-export`}>
      <span id={`${id}-export`} className="fa-synopsis-toolbar__label">{t('exportLabel')}</span>
      {EXPORTS.map(([format, key]) => <Button key={format} size="sm" onClick={() => onExport(format)}>{t(key)}</Button>)}
      {serverExports.map((link) => <a key={link.href} className="fa-button fa-button--secondary fa-button--sm" href={link.href} download="">{link.label}</a>)}
    </div>
  )
}

/** Werkzeugleiste der Synopse: Ansicht, Suche, Navigation, Filter, Exporte. */
export function SynopsisToolbar(props: SynopsisToolbarProps) {
  const { t } = props
  return (
    <div className="fa-synopsis-toolbar" role="region" aria-label={t('toolbar')}>
      <TopRow {...props} />
      <div className="fa-synopsis-toolbar__row">
        <Filters {...props} />
        <div className="fa-synopsis-toolbar__options">
          <label><input type="checkbox" checked={props.highlight} onChange={(event) => props.onHighlight(checked(event))} /> {t('highlight')}</label>
          {props.editable ? (
            <label><input type="checkbox" checked={props.onlySelected} onChange={(event) => props.onOnlySelected(checked(event))} /> {t('onlySelected')}</label>
          ) : null}
        </div>
        <Exports {...props} />
      </div>
    </div>
  )
}
