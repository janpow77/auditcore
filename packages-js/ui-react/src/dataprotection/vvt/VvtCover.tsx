import { useState } from 'react'
import { coverIssues, type Person, type RegisterContent, type RegisterIssue } from '@flowaudit/ui-core'
import { Button } from '../../base/Button'
import { TextField } from '../../base/TextField'
import { useDataProtectionText } from '../shared'

export interface VvtCoverProps {
  content: RegisterContent
  issues?: readonly RegisterIssue[]
  editing?: boolean
  onPersonChange: (part: 'verantwortlicher' | 'dsb', person: Person) => void
  onDepartmentsChange: (departments: string[]) => void
}

function People({ content, editing, onPersonChange }: VvtCoverProps) {
  const { t } = useDataProtectionText()
  const parts = [
    { part: 'verantwortlicher' as const, label: t('controller'), person: content.deckblatt.verantwortlicher ?? {} },
    { part: 'dsb' as const, label: t('dpo'), person: content.deckblatt.dsb ?? {} },
  ]
  return (
    <div className="fa-dataprotection__grid">
      {parts.map((entry) =>
        editing ? (
          <TextField key={entry.part} value={entry.person.name ?? ''} label={entry.label} required onChange={(name) => onPersonChange(entry.part, { name })} />
        ) : (
          <div key={entry.part} className="fa-dataprotection__field">
            <span className="fa-dataprotection__label">{entry.label}</span>
            <span>{entry.person.name || t('empty')}</span>
          </div>
        ),
      )}
    </div>
  )
}

function NewDepartment({ content, onDepartmentsChange }: VvtCoverProps) {
  const { t } = useDataProtectionText()
  const [fresh, setFresh] = useState('')
  function add(): void {
    const name = fresh.trim()
    if (!name || content.referate.includes(name)) return
    onDepartmentsChange([...content.referate, name])
    setFresh('')
  }
  return (
    <div className="fa-dataprotection__bar">
      <TextField
        value={fresh}
        onChange={setFresh}
        label={t('departmentNew')}
        hideLabel
        placeholder={t('departmentNew')}
        onKeyDown={(event) => {
          if (event.key !== 'Enter') return
          event.preventDefault()
          add()
        }}
      />
      <Button icon="plus" label={t('departmentAdd')} onClick={add} />
    </div>
  )
}

/** Deckblatt: Verantwortliche Stelle, DSB, Referate (wie VvtCover.vue). */
export function VvtCover(props: VvtCoverProps) {
  const { t } = useDataProtectionText()
  const { content, editing = false } = props
  const notes = coverIssues(props.issues ?? [])
  return (
    <section className="fa-dataprotection__panel" data-testid="vvt-cover" aria-label={t('cover')}>
      <h3>{t('cover')}</h3>
      <People {...props} />
      {notes.length ? (
        <ul className="fa-dataprotection__issues">
          {notes.map((issue) => <li key={issue.subject} className="is-blocking">{issue.message}</li>)}
        </ul>
      ) : null}
      <h4>{t('departments')}</h4>
      <ul className="fa-dataprotection__chips">
        {content.referate.map((name) => (
          <li key={name}>
            {name}{' '}
            {editing ? (
              <Button variant="ghost" size="sm" icon="close" iconOnly label={t('departmentRemove', { name })} onClick={() => props.onDepartmentsChange(content.referate.filter((entry) => entry !== name))} />
            ) : null}
          </li>
        ))}
      </ul>
      {editing ? <NewDepartment {...props} /> : null}
    </section>
  )
}
