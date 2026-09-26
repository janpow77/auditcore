/**
 * Role tab: `flowaudit:akteur` at pools and lanes (role from the profile's
 * catalogue plus free display name). For flow nodes it shows the role
 * inherited from the lane or pool.
 */

import type { CSSProperties } from 'react'
import { label, roleOf, rolesFor, type Actor } from '@auditcore/bpmn-flowaudit'
import { actorAfter, inheritedRole, isContainerType } from '@auditcore/bpmn-flowaudit/ui'
import { FaIcon } from '../../base/FaIcon'
import { useEditorContext, useEditorState, useSelectionState } from '../../context'
import { useI18n } from '../../i18n'
import { CommitField } from '../CommitField'

function RoleChoice({ actor, onUpdate }: { actor: Actor; onUpdate: (patch: Partial<Actor>) => void }) {
  const { t, locale } = useI18n()
  const { selection, profile, readonly } = useEditorContext()
  const { info } = useEditorState()
  const roles = rolesFor(profile(), info?.programmingPeriod)

  const choose = (code: string) => {
    onUpdate({ role: code || undefined })
    const role = roleOf(profile(), code)
    if (selection.element() && role && !selection.property('name')) selection.rename(label(role.label, locale))
  }

  return (
    <>
      <p className="fa-help">{t('props.role.help')}</p>
      <div className="fa-role-grid" role="radiogroup" aria-label={t('props.role.role')}>
        {roles.map((role) => (
          <button
            key={role.code}
            type="button"
            role="radio"
            className="fa-role-option"
            aria-checked={actor.role === role.code}
            disabled={readonly()}
            style={{ '--fa-role-fill': role.color.fill, '--fa-role-stroke': role.color.stroke } as CSSProperties}
            onClick={() => choose(actor.role === role.code ? '' : role.code)}
          >
            <FaIcon name={role.icon} size={20} />
            <span className="fa-role-option__short">{role.short}</span>
            <span className="fa-role-option__label">{label(role.label, locale)}</span>
          </button>
        ))}
      </div>
      <label className="fa-field fa-section">
        <span className="fa-label">{t('props.role.displayName')}</span>
        <CommitField className="fa-input" value={actor.displayName ?? ''} disabled={readonly()} onCommit={(text) => onUpdate({ displayName: text.trim() || undefined })} />
      </label>
    </>
  )
}

function Inherited() {
  const { t, locale } = useI18n()
  const { editor, profile } = useEditorContext()
  const { element } = useSelectionState()
  const inherited = element ? inheritedRole(editor.model(), element.id, profile(), locale, t) : null
  return (
    <>
      <p className="fa-help">{t('props.role.onlyContainers')}</p>
      {inherited ? <p className="fa-badge fa-badge--info">{t('props.role.inherited', inherited)}</p> : null}
    </>
  )
}

export function RoleTab() {
  const { selection } = useEditorContext()
  const { type, extensions } = useSelectionState()
  const actor = extensions.actor ?? {}
  return (
    <div className="fa-tab-role">
      {isContainerType(type ?? '') ? <RoleChoice actor={actor} onUpdate={(patch) => selection.write({ actor: actorAfter(actor, patch) })} /> : <Inherited />}
    </div>
  )
}
