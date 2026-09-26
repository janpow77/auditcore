import { Fragment, useState } from 'react'
import {
  completeness,
  completenessTone,
  groupByDepartment,
  issuesFor,
  type Activity,
  type Completeness,
  type DataProtectionTranslate,
  type RegisterContent,
  type RegisterIssue,
} from '@flowaudit/ui-core'
import { Badge } from '../../base/Badge'
import { Button } from '../../base/Button'
import { TextField } from '../../base/TextField'
import { useElementId } from '../../store'
import { useDataProtectionText } from '../shared'

export interface VvtActivityListProps {
  content: RegisterContent
  issues?: readonly RegisterIssue[]
  selected?: number | null
  editing?: boolean
  onActivitySelect: (index: number) => void
  onAdd: (department: string) => void
}

function stateLabel(t: DataProtectionTranslate, value: Completeness): string {
  if (value.blocking) return value.blocking === 1 ? t('missingOne') : t('missing', { count: value.blocking })
  if (value.hints) return value.hints === 1 ? t('hintOne') : t('hints', { count: value.hints })
  return t('complete')
}

function name(t: DataProtectionTranslate, activity: Activity): string {
  return (typeof activity.name === 'string' && activity.name.trim()) || t('unnamed')
}

function AddActivity({ content, onAdd }: VvtActivityListProps) {
  const { t } = useDataProtectionText()
  const selectId = useElementId('fa-vvt-department')
  const [department, setDepartment] = useState('')
  return (
    <div className="fa-dataprotection__field">
      <label htmlFor={selectId}>{t('colDepartment')}</label>
      <select id={selectId} value={department} onChange={(event) => setDepartment(event.target.value)}>
        <option value="">{t('withoutDepartment')}</option>
        {content.referate.map((entry) => <option key={entry} value={entry}>{entry}</option>)}
      </select>
      <Button icon="plus" label={t('addActivity')} onClick={() => onAdd(department)} />
    </div>
  )
}

/** Tätigkeiten je Referat mit Suche und Vollständigkeit (wie VvtActivityList.vue). */
export function VvtActivityList(props: VvtActivityListProps) {
  const { t } = useDataProtectionText()
  const { content, issues = [], selected = null } = props
  const [query, setQuery] = useState('')
  const groups = groupByDepartment(content, query)
  const heading = t('activities', { count: content.taetigkeiten.length })
  const state = (activity: Activity): Completeness => completeness(issuesFor(issues, activity))
  return (
    <nav className="fa-dataprotection__panel" aria-label={heading} data-testid="vvt-list">
      <h3>{heading}</h3>
      <TextField value={query} onChange={setQuery} type="search" label={t('search')} hideLabel placeholder={t('search')} />
      {!content.taetigkeiten.length ? <p className="fa-dataprotection__muted">{t('noActivities')}</p> : null}
      {content.taetigkeiten.length && !groups.length ? <p className="fa-dataprotection__muted">{t('noMatches')}</p> : null}
      {groups.map((group) => (
        <Fragment key={group.department}>
          <h4>{group.department || t('withoutDepartment')}</h4>
          <ul className="fa-vvt__list">
            {group.items.map((item) => (
              <li key={item.index}>
                <button type="button" className="fa-vvt__item" aria-current={item.index === selected ? 'true' : undefined} onClick={() => props.onActivitySelect(item.index)}>
                  <span>{name(t, item.activity)}</span>
                  <Badge tone={completenessTone(state(item.activity))}>{stateLabel(t, state(item.activity))}</Badge>
                </button>
              </li>
            ))}
          </ul>
        </Fragment>
      ))}
      {props.editing ? <AddActivity {...props} /> : null}
    </nav>
  )
}
