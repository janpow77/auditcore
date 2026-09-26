import { recommendationTone, statusTone, type DataProtectionProfile, type OverviewRow } from '@auditcore/ui-core'
import { Badge } from '../../base/Badge'
import { Button } from '../../base/Button'
import { statusLabel, useDataProtectionText } from '../shared'

export interface DsfaOverviewProps {
  rows?: readonly OverviewRow[]
  profile?: DataProtectionProfile | null
  selected?: string | null
  editable?: boolean
  busy?: boolean
  onOpen: (assessmentId: string) => void
  onStart: (activityId: string) => void
}

function State({ row }: { row: OverviewRow }) {
  const { t } = useDataProtectionText()
  if (!row.dsfa) return <span className="fa-dataprotection__muted">{t('noDsfa')}</span>
  return (
    <>
      <Badge tone={statusTone(row.dsfa.status)}>{`${statusLabel(t, row.dsfa.status)} · ${t('colVersion')} ${row.dsfa.version}`}</Badge>
      {row.dsfa.pruefung_erforderlich ? <Badge tone="danger">{t('reviewRequired')}</Badge> : null}
    </>
  )
}

function Result({ row, profile }: { row: OverviewRow; profile: DataProtectionProfile | null }) {
  const { t } = useDataProtectionText()
  const key = row.dsfa?.entscheidung
  if (!key) return <span>{t('empty')}</span>
  const title = profile?.decisions.find((entry) => entry.key === key)?.title ?? key
  return <Badge tone={recommendationTone(key)}>{title}</Badge>
}

function Action({ row, props }: { row: OverviewRow; props: DsfaOverviewProps }) {
  const { t } = useDataProtectionText()
  const dsfa = row.dsfa
  if (dsfa) return <Button size="sm" label={t('openAssessment')} ariaLabel={`${t('openAssessment')}: ${row.name}`} onClick={() => props.onOpen(dsfa.id)} />
  if (!(props.editable ?? true)) return null
  return (
    <Button size="sm" variant="primary" disabled={props.busy} label={t('startAssessment')} ariaLabel={`${t('startAssessment')}: ${row.name}`} onClick={() => props.onStart(row.id)} />
  )
}

function Row({ row, props }: { row: OverviewRow; props: DsfaOverviewProps }) {
  const { t } = useDataProtectionText()
  const current = !!row.dsfa && row.dsfa.id === props.selected
  return (
    <tr aria-current={current ? 'true' : undefined}>
      <th scope="row">{row.name}</th>
      <td>{row.referat || t('withoutDepartment')}</td>
      <td><State row={row} /></td>
      <td><Result row={row} profile={props.profile ?? null} /></td>
      <td><Action row={row} props={props} /></td>
    </tr>
  )
}

/** Übersicht der Tätigkeiten mit Stand und Ergebnis der Abschätzung. */
export function DsfaOverview(props: DsfaOverviewProps) {
  const { t } = useDataProtectionText()
  const rows = props.rows ?? []
  return (
    <section className="fa-dataprotection__panel" data-testid="dsfa-overview" aria-label={t('overview')}>
      <h3>{t('overview')}</h3>
      {rows.length ? (
        <table className="fa-dataprotection__table">
          <thead>
            <tr>
              <th scope="col">{t('colActivity')}</th>
              <th scope="col">{t('colDepartment')}</th>
              <th scope="col">{t('colState')}</th>
              <th scope="col">{t('colResult')}</th>
              <th scope="col"><span className="fa-sr-only">{t('colAction')}</span></th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => <Row key={row.id} row={row} props={props} />)}
          </tbody>
        </table>
      ) : (
        <p className="fa-dataprotection__muted">{t('noRegister')}</p>
      )}
    </section>
  )
}
