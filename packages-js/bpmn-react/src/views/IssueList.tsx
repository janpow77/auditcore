/** Validation issues grouped by severity with jump to the element. */

import { useState } from 'react'
import { issueMessage, severityLabel, type Severity, type ValidationIssue } from '@auditcore/bpmn-flowaudit'
import { countSeverity, filterIssues, ISSUE_ICONS, SEVERITIES } from '@auditcore/bpmn-flowaudit/ui'
import { FaIcon } from '../base/FaIcon'
import { useI18n } from '../i18n'

export interface IssueListProps {
  issues: ValidationIssue[]
  running?: boolean
  error?: string | null
  onJump?: (elementId: string) => void
}

export function IssueList({ issues, running, error, onJump }: IssueListProps) {
  const { t, locale } = useI18n()
  const [filter, setFilter] = useState<Severity | 'alle'>('alle')
  return (
    <section className="fa-issues" aria-label={t('issues.label')} aria-busy={Boolean(running)}>
      <div className="fa-issues__filter" role="group">
        <button type="button" className="fa-chip" aria-pressed={filter === 'alle'} onClick={() => setFilter('alle')}>{t('issues.filter.all')} {issues.length}</button>
        {SEVERITIES.map((severity) => (
          <button key={severity} type="button" className="fa-chip" aria-pressed={filter === severity} onClick={() => setFilter(severity)}>
            <FaIcon name={ISSUE_ICONS[severity]} size={14} />
            {severityLabel(severity, locale)} {countSeverity(issues, severity)}
          </button>
        ))}
      </div>
      {error ? <p className="fa-badge fa-badge--danger">{error}</p> : null}
      {!issues.length ? <p className="fa-help">{t('issues.none')}</p> : null}
      <ol className="fa-issues__list">
        {filterIssues(issues, filter).map((item, index) => (
          <li key={index} className={`fa-issue fa-issue--${item.severity}`}>
            <FaIcon name={ISSUE_ICONS[item.severity]} size={16} label={severityLabel(item.severity, locale)} />
            <div className="fa-issue__body">
              <p>{issueMessage(item, locale)}</p>
              <span className="fa-help">{item.ruleId}</span>
            </div>
            {item.elementId ? <button type="button" className="fa-btn fa-btn--ghost" onClick={() => onJump?.(item.elementId as string)}>{t('issues.jump')}</button> : null}
          </li>
        ))}
      </ol>
    </section>
  )
}
