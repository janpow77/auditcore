/**
 * Group overview of a folder (recursive): status distribution, legal basis
 * coverage, key requirement coverage (catalogue of the profile) and
 * collection issues.
 */

import { issueMessage, keyRequirements, localized, type GroupOverview as Overview, type ProfileData, type ValidationIssue } from '@auditcore/bpmn-flowaudit'
import { statusLabel } from '@auditcore/bpmn-flowaudit/ui'
import { classes } from '../hooks'
import { useI18n } from '../i18n'

export interface GroupOverviewProps {
  overview: Overview
  profile: ProfileData | null
  issues: ValidationIssue[]
  title: string
  onOpen?: (id: string) => void
}

function Cards({ overview }: { overview: Overview }) {
  const { t, locale } = useI18n()
  const percent = Math.round((overview.legalBasisCoverage ?? 0) * 100)
  return (
    <div className="fa-overview__cards">
      <div className="fa-card fa-overview__card">
        <span className="fa-label">{t('collection.overview.count')}</span>
        <strong className="fa-overview__number">{overview.count}</strong>
      </div>
      <div className="fa-card fa-overview__card">
        <span className="fa-label">{t('collection.overview.legal')}</span>
        <strong className="fa-overview__number">{overview.legalBasisCoverage === null ? '–' : `${percent} %`}</strong>
        <div className="fa-meter" role="meter" aria-valuenow={percent} aria-valuemin={0} aria-valuemax={100}><span style={{ width: `${percent}%` }} /></div>
        <span className="fa-help">{t('collection.overview.legalValue', { with: overview.activitiesWithLegalBasis, total: overview.activities, percent })}</span>
      </div>
      <div className="fa-card fa-overview__card">
        <span className="fa-label">{t('collection.overview.status')}</span>
        <ul className="fa-overview__status">
          {Object.entries(overview.statusDistribution).map(([code, count]) => (
            <li key={code}><span className="fa-badge">{statusLabel(code, t, locale)}</span> {count}</li>
          ))}
        </ul>
      </div>
    </div>
  )
}

export function GroupOverview({ overview, profile, issues, title, onOpen }: GroupOverviewProps) {
  const { t, locale } = useI18n()
  const covered = (number: number) => overview.keyRequirementCoverage[number] ?? []
  return (
    <section className="fa-overview" aria-label={t('collection.overview')}>
      <h2>{title}</h2>
      <Cards overview={overview} />
      <h3 className="fa-section__title fa-section">{t('collection.overview.ka')}</h3>
      <div className="fa-overview__ka">
        {keyRequirements(profile).map((requirement) => (
          <div key={requirement.number} className={classes('fa-overview__ka-cell', covered(requirement.number).length > 0 && 'fa-overview__ka-cell--covered')} title={localized(requirement.title, locale)}>
            <strong>KA {requirement.number}</strong>
            <span>{covered(requirement.number).length}</span>
          </div>
        ))}
      </div>
      {overview.expired.length ? (
        <>
          <h3 className="fa-section__title fa-section">{t('collection.overview.expired')}</h3>
          {overview.expired.map((id) => (
            <button key={id} type="button" className="fa-chip" onClick={() => onOpen?.(id)}>{id}</button>
          ))}
        </>
      ) : null}
      {issues.length ? (
        <>
          <h3 className="fa-section__title fa-section">{t('collection.overview.issues')}</h3>
          <ul className="fa-overview__issues">
            {issues.map((item, index) => (
              <li key={index}>{issueMessage(item, locale)}</li>
            ))}
          </ul>
        </>
      ) : null}
    </section>
  )
}
