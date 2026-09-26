/**
 * Toolbar in one row with groups File · Edit · View · Check · Modes (legacy
 * `BpmnToolbar`): name, unsaved/readonly state, save, colour menu, flow
 * direction, page view and panel toggles. Actions are reported as `onAction`.
 */

import type { ChangeEvent } from 'react'
import { PALETTE_COLORS, type Direction, type PaletteColor } from '@flowaudit/bpmn-flowaudit'
import { actionDisabled, FILE_ACTIONS, PAGE_OPTIONS, VIEW_ACTIONS, type ToolbarAction } from '@flowaudit/bpmn-flowaudit/ui'
import { ColorSwatches } from '../base/ColorSwatches'
import { FaIcon } from '../base/FaIcon'
import { ToolbarMenu } from '../base/ToolbarMenu'
import { useI18n } from '../i18n'
import { CheckMenu, EditButtons, ModeButtons, NameField } from './ToolbarParts'

export interface EditorToolbarProps {
  name: string
  dirty: boolean
  saving: boolean
  readonly: boolean
  canUndo: boolean
  canRedo: boolean
  direction: Direction
  pageView: string
  active: Partial<Record<ToolbarAction, boolean>>
  hidden?: ToolbarAction[]
  palette?: readonly PaletteColor[]
  onAction: (action: ToolbarAction) => void
  onNameChange?: (value: string) => void
  onColor?: (color: PaletteColor | null) => void
  onDirection?: (value: Direction) => void
  onPageView?: (value: string) => void
  onImportFile?: (file: File) => void
}

function FileActions({ props }: { props: EditorToolbarProps }) {
  const { t } = useI18n()
  const visible = (id: ToolbarAction) => !props.hidden?.includes(id)
  const onFile = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) props.onImportFile?.(file)
    event.target.value = ''
  }
  return FILE_ACTIONS.map((entry) => {
    if (entry.id === 'import') {
      return visible('import') ? (
        <label key={entry.id} className="fa-icon-btn" title={t(entry.label)} aria-disabled={props.readonly}>
          <FaIcon name={entry.icon} />
          <span className="fa-sr-only">{t(entry.label)}</span>
          <input type="file" accept=".bpmn,.xml" className="fa-sr-only" disabled={props.readonly} onChange={onFile} />
        </label>
      ) : null
    }
    return visible(entry.id) ? (
      <button key={entry.id} type="button" className="fa-icon-btn" aria-label={t(entry.label)} title={t(entry.label)} onClick={() => props.onAction(entry.id)}>
        <FaIcon name={entry.icon} />
      </button>
    ) : null
  })
}

function DirectionGroup({ props }: { props: EditorToolbarProps }) {
  const { t } = useI18n()
  const button = (value: Direction, icon: string, label: string) => (
    <button type="button" className="fa-icon-btn" aria-pressed={props.direction === value} title={t(label)} aria-label={t(label)} disabled={props.readonly} onClick={() => props.onDirection?.(value)}>
      <FaIcon name={icon} />
    </button>
  )
  return (
    <div className="fa-segmented" role="group" aria-label={t('toolbar.direction')}>
      {button('waagerecht', 'horizontal', 'toolbar.horizontal')}
      {button('senkrecht', 'vertical', 'toolbar.vertical')}
    </div>
  )
}

function ViewGroup({ props }: { props: EditorToolbarProps }) {
  const { t } = useI18n()
  return (
    <>
      {VIEW_ACTIONS.map((entry) => (
        <button key={entry.id} type="button" className="fa-icon-btn" aria-label={t(entry.label)} title={t(entry.label)} onClick={() => props.onAction(entry.id)}>
          <FaIcon name={entry.icon} />
        </button>
      ))}
      <select className="fa-select fa-toolbar__page" value={props.pageView} aria-label={t('toolbar.pageView')} onChange={(event) => props.onPageView?.(event.target.value)}>
        <option value="aus">{t('toolbar.pageOff')}</option>
        {PAGE_OPTIONS.map((option) => (
          <option key={option.value} value={option.value}>{option.label}</option>
        ))}
      </select>
    </>
  )
}

export function EditorToolbar(props: EditorToolbarProps) {
  const { t } = useI18n()
  const disabled = (id: ToolbarAction, writes?: boolean) => actionDisabled(id, writes, props)
  return (
    <div className="fa-toolbar" role="toolbar" aria-label={t('toolbar.label')}>
      <button type="button" className="fa-icon-btn" aria-pressed={props.active['left-panel']} aria-label={t('toolbar.leftPanel')} title={t('toolbar.leftPanel')} onClick={() => props.onAction('left-panel')}>
        <FaIcon name="panel-left" />
      </button>
      <NameField name={props.name} readonly={props.readonly} onNameChange={props.onNameChange} />
      {props.dirty ? <span className="fa-badge fa-badge--warning">{t('editor.unsaved')}</span> : null}
      {props.readonly ? <span className="fa-badge fa-badge--info"><FaIcon name="lock" size={12} />{t('editor.readonly')}</span> : null}
      <button type="button" className="fa-btn fa-btn--primary" disabled={props.saving || props.readonly} onClick={() => props.onAction('save')}>
        <FaIcon name="save" size={16} />
        {t('toolbar.save')}
      </button>
      <span className="fa-toolbar__sep" />
      <FileActions props={props} />
      <span className="fa-toolbar__sep" />
      <EditButtons disabled={disabled} onAction={props.onAction} />
      <ToolbarMenu label={t('toolbar.color')} icon="color">
        {(close) => (
          <>
            <p className="fa-menu-hint">{t('toolbar.colorHint')}</p>
            <ColorSwatches colors={props.palette ?? PALETTE_COLORS} disabled={props.readonly} onChoose={(color) => (props.onColor?.(color), close())} />
          </>
        )}
      </ToolbarMenu>
      <DirectionGroup props={props} />
      <span className="fa-toolbar__sep" />
      <ViewGroup props={props} />
      <span className="fa-toolbar__sep" />
      <CheckMenu hidden={props.hidden} disabled={disabled} onAction={props.onAction} />
      <ModeButtons hidden={props.hidden} active={props.active} onAction={props.onAction} />
      <span className="fa-toolbar__spacer" />
      <button type="button" className="fa-icon-btn" aria-label={t('toolbar.theme')} title={t('toolbar.theme')} onClick={() => props.onAction('theme')}>
        <FaIcon name="moon" />
      </button>
      <button type="button" className="fa-icon-btn" aria-pressed={props.active['right-panel']} aria-label={t('toolbar.rightPanel')} title={t('toolbar.rightPanel')} onClick={() => props.onAction('right-panel')}>
        <FaIcon name="panel-right" />
      </button>
    </div>
  )
}
