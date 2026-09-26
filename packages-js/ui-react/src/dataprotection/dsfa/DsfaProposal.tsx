import { decisionTitle, recommendationTone, type DataProtectionProfile, type Proposal } from '@flowaudit/ui-core'
import { Badge } from '../../base/Badge'
import { prefixedLabel, useDataProtectionText } from '../shared'

export interface DsfaProposalProps {
  profile: DataProtectionProfile
  proposal: Proposal
  preview?: boolean
  openPoints?: readonly string[]
}

function Issues({ proposal, openPoints }: { proposal: Proposal; openPoints: readonly string[] }) {
  const { t } = useDataProtectionText()
  if (!proposal.issues.length && !openPoints.length) return null
  return (
    <>
      <h4>{t('issuesTitle')}</h4>
      <ul className="fa-dataprotection__issues">
        {proposal.issues.map((issue) => <li key={issue.code + issue.subject} className={issue.blocking ? 'is-blocking' : undefined}>{issue.message}</li>)}
        {openPoints.map((point) => <li key={point}>{point}</li>)}
      </ul>
    </>
  )
}

/** Vorschlag der Bibliothek (Empfehlung, Begründung, Konsultationshinweis, offene Punkte). */
export function DsfaProposal({ profile, proposal, preview = false, openPoints = [] }: DsfaProposalProps) {
  const { t } = useDataProtectionText()
  const title = prefixedLabel(t, 'recommendation', proposal.recommendation, decisionTitle(profile, proposal.recommendation))
  return (
    <section className="fa-dataprotection__panel" data-testid="dsfa-proposal" aria-label={t('proposalTitle')}>
      <div className="fa-dataprotection__bar">
        <h3>{t('proposalTitle')}</h3>
        <Badge tone={recommendationTone(proposal.recommendation)}>{title}</Badge>
        {preview ? <Badge tone="accent">{t('preview')}</Badge> : null}
      </div>
      <p aria-live="polite">{proposal.recommendation_text}</p>
      <p className="fa-dataprotection__muted">{proposal.reasoning}</p>
      {proposal.consultation_notice ? (
        <p className="fa-dataprotection__alert fa-dataprotection__alert--info">
          <strong>{t('consultation')}:</strong> {proposal.consultation_notice.text}
        </p>
      ) : null}
      <Issues proposal={proposal} openPoints={openPoints} />
      <p className="fa-dataprotection__muted">{t('profile', { id: proposal.profile.id, version: proposal.profile.version })}</p>
    </section>
  )
}
