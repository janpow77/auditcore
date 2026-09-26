/** Parts of the editor toolbar: name field, undo/redo, check menu and mode toggles. */

import { useEffect, useState } from 'react'
import { CHECK_ACTIONS, EDIT_ACTIONS, MODE_ACTIONS, type ToolbarAction } from '@flowaudit/bpmn-flowaudit/ui'
import { FaIcon } from '../base/FaIcon'
import { ToolbarMenu } from '../base/ToolbarMenu'
import { useI18n } from '../i18n'

type Disabled = (id: ToolbarAction, writes?: boolean) => boolean

/** Diagram name; like Vue's `@change` it reports on leaving the field or Enter. */
export function NameField({ name, readonly, onNameChange }: { name: string; readonly: boolean; onNameChange?: (value: string) => void }) {
  const { t } = useI18n()
  const [draft, setDraft] = useState(name)
  useEffect(() => setDraft(name), [name])
  const commit = () => draft !== name && onNameChange?.(draft)
  return (
    <input
      className="fa-input fa-toolbar__name"
      value={draft}
      aria-label={t('props.name')}
      readOnly={readonly}
      onChange={(event) => setDraft(event.target.value)}
      onBlur={commit}
      onKeyDown={(event) => event.key === 'Enter' && commit()}
    />
  )
}

export function EditButtons({ disabled, onAction }: { disabled: Disabled; onAction: (action: ToolbarAction) => void }) {
  const { t } = useI18n()
  return EDIT_ACTIONS.map((entry) => (
    <button key={entry.id} type="button" className="fa-icon-btn" disabled={disabled(entry.id, entry.writes)} aria-label={t(entry.label)} title={t(entry.label)} onClick={() => onAction(entry.id)}>
      <FaIcon name={entry.icon} />
    </button>
  ))
}

export function CheckMenu({ hidden, disabled, onAction }: { hidden?: ToolbarAction[]; disabled: Disabled; onAction: (action: ToolbarAction) => void }) {
  const { t } = useI18n()
  return (
    <ToolbarMenu label={t('toolbar.check')} icon="validate" showLabel>
      {(close) =>
        CHECK_ACTIONS.filter((entry) => !hidden?.includes(entry.id)).map((entry) => (
          <button key={entry.id} type="button" role="menuitem" className="fa-menu-item" disabled={disabled(entry.id, entry.writes)} onClick={() => (onAction(entry.id), close())}>
            <FaIcon name={entry.icon} />
            <span>
              {t(entry.label)}
              {entry.hint ? <span className="fa-menu-hint">{t(entry.hint)}</span> : null}
            </span>
          </button>
        ))
      }
    </ToolbarMenu>
  )
}

export function ModeButtons({ hidden, active, onAction }: { hidden?: ToolbarAction[]; active: Partial<Record<ToolbarAction, boolean>>; onAction: (action: ToolbarAction) => void }) {
  const { t } = useI18n()
  return (
    <div className="fa-toolbar__modes">
      {MODE_ACTIONS.filter((entry) => !hidden?.includes(entry.id)).map((entry) => (
        <button key={entry.id} type="button" className="fa-icon-btn" aria-pressed={Boolean(active[entry.id])} aria-label={t(entry.label)} title={t(entry.label)} onClick={() => onAction(entry.id)}>
          <FaIcon name={entry.icon} />
        </button>
      ))}
    </div>
  )
}
