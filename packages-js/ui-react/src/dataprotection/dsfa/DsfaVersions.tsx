import { decisionTitle, type AssessmentSummary, type DataProtectionProfile } from '@auditcore/ui-core'
import { Button } from '../../base/Button'
import { statusLabel, useDataProtectionText } from '../shared'

export interface DsfaVersionsProps {
  versions?: readonly AssessmentSummary[]
  profile: DataProtectionProfile
  current?: string
  onOpen: (id: string) => void
}

function VersionRow({ entry, props }: { entry: AssessmentSummary; props: DsfaVersionsProps }) {
  const { t, when } = useDataProtectionText()
  const at = (value: string | null): string => when(value) || t('empty')
  const current = entry.id === props.current
  return (
    <tr aria-current={current ? 'true' : undefined}>
      <td>{entry.version}</td>
      <td>{statusLabel(t, entry.status)}</td>
      <td>{decisionTitle(props.profile, entry.decision) || t('empty')}</td>
      <td>{at(entry.created_at)}</td>
      <td>{entry.released_by ? `${entry.released_by}, ${at(entry.released_at)}` : t('empty')}</td>
      <td>
        {current ? null : (
          <Button size="sm" variant="ghost" label={t('openAssessment')} ariaLabel={`${t('openAssessment')}: ${t('colVersion')} ${entry.version}`} onClick={() => props.onOpen(entry.id)} />
        )}
      </td>
    </tr>
  )
}

/** Fassungen der Abschätzung mit Entscheidung und Freigabe. */
export function DsfaVersions(props: DsfaVersionsProps) {
  const { t } = useDataProtectionText()
  return (
    <section className="fa-dataprotection__panel" data-testid="dsfa-versions" aria-label={t('versions')}>
      <h3>{t('versions')}</h3>
      <table className="fa-dataprotection__table">
        <thead>
          <tr>
            <th scope="col">{t('colVersion')}</th>
            <th scope="col">{t('colStatus')}</th>
            <th scope="col">{t('colDecision')}</th>
            <th scope="col">{t('colCreated')}</th>
            <th scope="col">{t('colReleased')}</th>
            <th scope="col"><span className="fa-sr-only">{t('colAction')}</span></th>
          </tr>
        </thead>
        <tbody>
          {(props.versions ?? []).map((entry) => <VersionRow key={entry.id} entry={entry} props={props} />)}
        </tbody>
      </table>
    </section>
  )
}
