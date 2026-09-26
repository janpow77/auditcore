import { Fragment } from 'react'
import { displayValue, fieldIssues, type Activity, type FieldValue, type RegisterColumn, type RegisterIssue } from '@auditcore/ui-core'
import { Button } from '../../base/Button'
import { classes } from '../../store'
import { useDataProtectionText } from '../shared'
import { VvtField } from './VvtField'

export interface VvtActivityDetailProps {
  activity: Activity
  columns?: readonly RegisterColumn[]
  issues?: readonly RegisterIssue[]
  departments?: readonly string[]
  editing?: boolean
  onFieldChange: (key: string, value: FieldValue) => void
  onRemove: () => void
}

function ReadView({ activity, columns = [], issues = [] }: VvtActivityDetailProps) {
  const { t } = useDataProtectionText()
  const texts = { yes: t('yes'), no: t('no'), empty: t('empty') }
  return (
    <dl className="fa-dataprotection__dl">
      {columns.map((column) => (
        <Fragment key={column.key}>
          <dt>
            {column.title}
            <br />
            <span className="fa-dataprotection__ref">{column.reference}</span>
          </dt>
          <dd>
            {displayValue(activity[column.key], texts)}
            {fieldIssues(issues, activity, column.key).map((issue) => (
              <span key={issue.message} className={classes('fa-dataprotection__note', issue.blocking && 'fa-dataprotection__note--blocking')}>
                <br />
                {issue.message}
              </span>
            ))}
          </dd>
        </Fragment>
      ))}
    </dl>
  )
}

/** Eine Tätigkeit: Felder bearbeiten oder lesen (wie VvtActivityDetail.vue). */
export function VvtActivityDetail(props: VvtActivityDetailProps) {
  const { t } = useDataProtectionText()
  const { activity, columns = [], issues = [], departments = [], editing = false } = props
  const title = (typeof activity.name === 'string' && activity.name.trim()) || t('unnamed')
  return (
    <article className="fa-dataprotection__panel" data-testid="vvt-detail" aria-label={title}>
      <div className="fa-dataprotection__bar">
        <h3>{title}</h3>
        {activity.id ? <span className="fa-dataprotection__muted">{activity.id}</span> : null}
        {editing ? (
          <div className="fa-dataprotection__actions">
            <Button variant="ghost" size="sm" icon="trash" label={t('removeActivity')} onClick={props.onRemove} />
          </div>
        ) : null}
      </div>
      {editing ? (
        <div className="fa-dataprotection__grid">
          {columns.map((column) => (
            <VvtField
              key={column.key}
              column={column}
              value={activity[column.key] ?? null}
              issues={fieldIssues(issues, activity, column.key)}
              departments={departments}
              onValueChange={(value) => props.onFieldChange(column.key, value)}
            />
          ))}
        </div>
      ) : (
        <ReadView {...props} />
      )}
    </article>
  )
}
