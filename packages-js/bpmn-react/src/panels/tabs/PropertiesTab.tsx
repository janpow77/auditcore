/**
 * Audit attributes: name/value properties defined by the profile
 * (`camunda:property`). Single choices as select, several values as check
 * boxes, yes/no as one check box, free text on blur. An empty value removes
 * the property; properties the profile does not know stay untouched.
 */

import type { PropertyPatch } from '@auditcore/bpmn-flowaudit'
import { isYes, propertyFields, textPatch, togglePatch, yesNoPatch, type PropertyField } from '@auditcore/bpmn-flowaudit/ui'
import { useEditorContext, useSelectionState } from '../../context'
import { classes } from '../../hooks'
import { useI18n } from '../../i18n'
import { CommitField } from '../CommitField'

interface FieldProps {
  field: PropertyField
  disabled: boolean
  write: (patch: PropertyPatch) => void
}

function ChoiceField({ field, disabled, write }: FieldProps) {
  const { t } = useI18n()
  return (
    <select className="fa-select" value={field.selected[0] ?? ''} disabled={disabled} aria-labelledby={`fa-prop-${field.name}`} onChange={(event) => write(textPatch(field, event.target.value))}>
      <option value="">{t('props.properties.none')}</option>
      {field.options.map((option) => (
        <option key={option.value} value={option.value}>
          {option.known ? option.label : `${option.label} (${t('props.properties.unknown')})`}
        </option>
      ))}
    </select>
  )
}

function MultiChoiceField({ field, disabled, write }: FieldProps) {
  const { t } = useI18n()
  return (
    <div className="fa-property__choices" role="group" aria-labelledby={`fa-prop-${field.name}`}>
      {field.options.map((option) => (
        <label key={option.value} className="fa-check">
          <input type="checkbox" checked={field.selected.includes(option.value)} disabled={disabled} onChange={() => write(togglePatch(field, option.value))} />
          {option.label}
          {option.known ? null : <span className="fa-badge">{t('props.properties.unknown')}</span>}
        </label>
      ))}
    </div>
  )
}

function FieldInput(props: FieldProps) {
  const { t } = useI18n()
  const { field, disabled, write } = props
  if (field.kind === 'choice') return <ChoiceField {...props} />
  if (field.kind === 'multi_choice') return <MultiChoiceField {...props} />
  if (field.kind === 'yes_no') {
    return (
      <label className="fa-check">
        <input type="checkbox" checked={isYes(field)} disabled={disabled} aria-labelledby={`fa-prop-${field.name}`} onChange={(event) => write(yesNoPatch(field, event.target.checked))} />
        {t('props.properties.yes')}
      </label>
    )
  }
  return <CommitField className="fa-input" value={field.text} disabled={disabled} aria-labelledby={`fa-prop-${field.name}`} onCommit={(raw) => write(textPatch(field, raw))} />
}

export function PropertiesTab() {
  const { t, locale } = useI18n()
  const { selection, profile, readonly } = useEditorContext()
  const { type } = useSelectionState()
  const fields = propertyFields(profile(), type, selection.namedProperties(), locale)
  const labelOf = (name: string) => fields.find((field) => field.name === name)?.label ?? name
  const inactiveHint = (field: PropertyField) => {
    const condition = profile()?.properties?.entries.find((entry) => entry.name === field.name)?.depends_on
    return condition ? t('props.properties.inactive', { property: labelOf(condition.property), values: condition.values.join(', ') }) : ''
  }
  const write = (patch: PropertyPatch) => selection.writeProperties(patch)

  return (
    <div className="fa-tab-properties">
      <p className="fa-help">{t('props.properties.help')}</p>
      {fields.map((field) => (
        <div key={field.name} className={classes('fa-field fa-property', !field.active && 'fa-property--inactive')}>
          <span id={`fa-prop-${field.name}`} className="fa-label">
            {field.label}
          </span>
          <FieldInput field={field} disabled={readonly()} write={write} />
          {field.help ? <span className="fa-help">{field.help}</span> : null}
          {field.active ? null : <span className="fa-help fa-property__hint">{inactiveHint(field)}</span>}
        </div>
      ))}
    </div>
  )
}
