import { useEffect, useState, type ChangeEvent } from 'react'
import { parseCount, type FieldValue, type RegisterColumn, type RegisterIssue } from '@auditcore/ui-core'
import { classes, useElementId } from '../../store'
import { useDataProtectionText } from '../shared'

export interface VvtFieldProps {
  column: RegisterColumn
  value?: FieldValue
  issues?: readonly RegisterIssue[]
  departments?: readonly string[]
  onValueChange: (value: FieldValue) => void
}

const SHORT_FIELDS = ['name', 'referat', 'ansprechperson']
const CHOICES = ['yes', 'no', 'open'] as const

function flagValue(choice: (typeof CHOICES)[number]): boolean | null {
  return choice === 'yes' ? true : choice === 'no' ? false : null
}

function Notes({ id, issues, countError }: { id: string; issues: readonly RegisterIssue[]; countError?: boolean }) {
  const { t } = useDataProtectionText()
  if (!issues.length && !countError) return null
  return (
    <div id={id}>
      {countError ? <p className="fa-dataprotection__note fa-dataprotection__note--blocking">{t('invalidCount')}</p> : null}
      {issues.map((issue) => (
        <p key={issue.code + issue.message} className={classes('fa-dataprotection__note', issue.blocking && 'fa-dataprotection__note--blocking')}>{issue.message}</p>
      ))}
    </div>
  )
}

function FlagField({ column, value = null, issues = [], onValueChange }: VvtFieldProps) {
  const { t } = useDataProtectionText()
  const id = useElementId('fa-vvt-field')
  const blocking = issues.some((issue) => issue.blocking)
  return (
    <fieldset className={classes('fa-dataprotection__field', column.required && 'fa-dataprotection__field--required')} aria-describedby={issues.length ? `${id}-note` : undefined}>
      <legend>{column.title}</legend>
      <div className="fa-dataprotection__choices">
        {CHOICES.map((choice) => (
          <label key={choice} className="fa-dataprotection__choice">
            <input type="radio" name={id} checked={value === flagValue(choice)} aria-invalid={blocking ? 'true' : undefined} onChange={() => onValueChange(flagValue(choice))} /> {t(choice)}
          </label>
        ))}
      </div>
      {column.reference ? <span className="fa-dataprotection__ref">{column.reference}</span> : null}
      <Notes id={`${id}-note`} issues={issues} />
    </fieldset>
  )
}

function useCount(value: FieldValue, onValueChange: (value: FieldValue) => void) {
  const [text, setText] = useState(value === null || value === undefined ? '' : String(value))
  const [error, setError] = useState(false)
  useEffect(() => {
    setText(value === null || value === undefined ? '' : String(value))
    setError(false)
  }, [value])
  function change(event: ChangeEvent<HTMLInputElement>): void {
    setText(event.target.value)
    const parsed = parseCount(event.target.value)
    setError(parsed === undefined)
    if (parsed !== undefined) onValueChange(parsed)
  }
  return { text, error, change }
}

function Control({ id, column, value, blocking, described, count, departments, onText }: {
  id: string; column: RegisterColumn; value: FieldValue; blocking: boolean; described: string | undefined
  count: ReturnType<typeof useCount>; departments: readonly string[]; onText: (event: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => void
}) {
  const text = typeof value === 'string' ? value : ''
  if (column.kind === 'count') {
    return <input id={id} type="text" inputMode="numeric" value={count.text} aria-invalid={blocking || count.error ? 'true' : undefined} aria-describedby={described} onChange={count.change} />
  }
  if (!SHORT_FIELDS.includes(column.key)) {
    return <textarea id={id} rows={2} value={text} required={column.required} aria-invalid={blocking ? 'true' : undefined} aria-describedby={described} onChange={onText} />
  }
  const isDepartment = column.key === 'referat'
  return (
    <>
      <input id={id} type="text" value={text} list={isDepartment ? `${id}-list` : undefined} required={column.required} aria-invalid={blocking ? 'true' : undefined} aria-describedby={described} onChange={onText} />
      {isDepartment ? <datalist id={`${id}-list`}>{departments.map((department) => <option key={department} value={department} />)}</datalist> : null}
    </>
  )
}

function InputField(props: VvtFieldProps) {
  const { column, value = null, issues = [], departments = [], onValueChange } = props
  const id = useElementId('fa-vvt-field')
  const count = useCount(value, onValueChange)
  const blocking = issues.some((issue) => issue.blocking)
  const described = issues.length || count.error ? `${id}-note` : undefined
  return (
    <div className={classes('fa-dataprotection__field', column.required && 'fa-dataprotection__field--required')}>
      <label htmlFor={id}>{column.title}</label>
      <Control id={id} column={column} value={value} blocking={blocking} described={described} count={count} departments={departments} onText={(event) => onValueChange(event.target.value)} />
      {column.reference ? <span className="fa-dataprotection__ref">{column.reference}</span> : null}
      <Notes id={`${id}-note`} issues={issues} countError={count.error} />
    </div>
  )
}

/** Ein Feld einer Tätigkeit je nach Spaltenart (Text, Ja/Nein/offen, Anzahl) wie VvtField.vue. */
export function VvtField(props: VvtFieldProps) {
  return props.column.kind === 'flag' ? <FlagField {...props} /> : <InputField {...props} />
}
