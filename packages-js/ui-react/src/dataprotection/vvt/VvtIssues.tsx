import { completeness, type RegisterIssue } from '@auditcore/ui-core'
import { useDataProtectionText } from '../shared'

/** Ergebnis der Vollständigkeitsprüfung der Bibliothek (wie VvtIssues.vue). */
export function VvtIssues({ issues = [] }: { issues?: readonly RegisterIssue[] }) {
  const { t } = useDataProtectionText()
  const summary = completeness(issues)
  return (
    <section className="fa-dataprotection__panel" data-testid="vvt-issues" aria-label={t('completenessTitle')}>
      <h3>{t('completenessTitle')}</h3>
      <p aria-live="polite">{issues.length ? t('completenessSummary', { blocking: summary.blocking, hints: summary.hints }) : t('completenessOk')}</p>
      {issues.length ? (
        <ul className="fa-dataprotection__issues">
          {issues.map((issue) => (
            <li key={issue.subject + issue.code} className={issue.blocking ? 'is-blocking' : undefined}>
              <strong>{issue.blocking ? t('blockingLabel') : t('hintLabel')}:</strong> {issue.message}
            </li>
          ))}
        </ul>
      ) : null}
    </section>
  )
}
