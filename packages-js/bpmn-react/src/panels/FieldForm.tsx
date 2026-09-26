/**
 * Renders one object from declarative field descriptions. Reports the whole
 * updated object on every committed change (blur/Enter for text fields).
 */

import { fieldText, inputType, isWide, parseFieldInput, unknownOption, withField, type FieldDescriptor, type Option } from '@auditcore/bpmn-flowaudit/ui'
import { useElementId } from '../hooks'
import { useI18n } from '../i18n'
import { CommitField } from './CommitField'

type Row = Record<string, unknown>

export interface FieldFormProps {
  value: Row
  fields: FieldDescriptor[]
  optionsFor: (field: FieldDescriptor) => Option[]
  disabled?: boolean
  onUpdate: (value: Row) => void
}

interface FieldProps extends Omit<FieldFormProps, 'fields'> {
  field: FieldDescriptor
  labelId: string
}

function SelectField({ value, field, optionsFor, disabled, onUpdate, labelId }: FieldProps) {
  const { t } = useI18n()
  const text = fieldText(value, field)
  const options = optionsFor(field)
  const unknown = unknownOption(options, text)
  return (
    <select className="fa-select" value={text} disabled={disabled} aria-labelledby={labelId} onChange={(event) => onUpdate(withField(value, field.key, event.target.value))}>
      <option value="">{t('common.none')}</option>
      {options.map((option) => (
        <option key={option.value} value={option.value}>{option.label}</option>
      ))}
      {unknown ? <option value={text}>{text}</option> : null}
    </select>
  )
}

function Field(props: FieldProps) {
  const { t } = useI18n()
  const { value, field, disabled, onUpdate, labelId } = props
  if (field.kind === 'checkbox') {
    return (
      <span className="fa-check">
        <input type="checkbox" checked={Boolean(value[field.key])} disabled={disabled} onChange={(event) => onUpdate(withField(value, field.key, event.target.checked))} />
        {t(field.label)}
      </span>
    )
  }
  const commit = (raw: string) => onUpdate(withField(value, field.key, parseFieldInput(field, raw)))
  const text = fieldText(value, field)
  return (
    <>
      <span id={labelId} className="fa-label">{t(field.label)}</span>
      {field.kind === 'select' ? (
        <SelectField {...props} />
      ) : field.kind === 'textarea' ? (
        <CommitField multiline className="fa-textarea" rows={3} value={text} disabled={disabled} placeholder={field.placeholder} onCommit={commit} />
      ) : (
        <CommitField className="fa-input" type={inputType(field)} value={text} disabled={disabled} placeholder={field.placeholder} onCommit={commit} />
      )}
    </>
  )
}

export function FieldForm({ fields, ...props }: FieldFormProps) {
  const uid = useElementId('fa-field')
  return (
    <div className="fa-grid-2 fa-field-form">
      {fields.map((field) => (
        <label key={field.key} className={isWide(field) ? 'fa-field fa-field--wide' : 'fa-field'}>
          <Field {...props} field={field} labelId={`${uid}-${field.key}`} />
        </label>
      ))}
    </div>
  )
}
