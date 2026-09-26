import {
  profileHintText,
  profileStatusText,
  type Evaluation,
  type ProfileReference,
  type RiskTranslate,
  type Locale,
  type ProfileDetail,
  type RiskFilter,
  type RiskPort,
} from '@auditcore/ui-core'
import { RiskFlagFilter } from './RiskFlagFilter'
import { RiskFlagSummary } from './RiskFlagSummary'
import { RiskFlagTable } from './RiskFlagTable'
import { RiskProfileInfo } from './RiskProfileInfo'
import { RiskRecordDetail } from './RiskRecordDetail'
import { useRiskFlags } from './useRiskFlags'

export interface FlowauditRiskFlagsProps {
  /** Antwort von `POST /evaluate` (auditcore_risk.web, docs/ui/risk-rest.md). */
  evaluation?: Evaluation | null
  /** Antwort von `GET /profiles/{id}/{version}`; ohne sie entfällt die Profilansicht. */
  profile?: ProfileDetail | null
  /** Optional: lädt die Profilbeschreibung nach, wenn `profile` fehlt (`createRiskRestPort`). */
  port?: RiskPort | null
  heading?: string
  locale?: Locale
  /** Gewählter Datensatz (Index) oder `null` nach erneutem Klick (Vue: `record-select`). */
  onRecordSelect?: (index: number | null) => void
  /** Neuer Filter (Vue: `filter-change`). */
  onFilterChange?: (filter: RiskFilter) => void
}

function RiskHead({ heading, reference, t }: { heading: string; reference: ProfileReference | null; t: RiskTranslate }) {
  const hint = profileHintText(reference, t)
  return (
    <header className="fa-risk__head">
      <h2>{heading || t('title')}</h2>
      {reference ? (
        <p className="fa-risk__profile" data-testid="risk-profile">
          {t('profile')} <code>{reference.id}</code> · {t('version')} <code>{reference.version}</code> · {profileStatusText(reference, t)}
        </p>
      ) : null}
      {hint ? <p className="fa-risk__hint" role="note">{hint}</p> : null}
    </header>
  )
}

function ProfileSection({ error, profile, t, locale }: { error: string; profile: ProfileDetail | null; t: RiskTranslate; locale?: Locale }) {
  return (
    <>
      {error ? <p className="fa-risk__hint" role="alert">{error}</p> : null}
      {profile ? (
        <details className="fa-risk__profile-info">
          <summary>{t('profileInfo')}</summary>
          <RiskProfileInfo profile={profile} locale={locale} />
        </details>
      ) : null}
    </>
  )
}

/**
 * Risiko-Merkmale als native React-Komponente – Vertrag, Texte und Markup wie
 * `<flowaudit-risk-flags>`: Verteilung je Merkmal, Filter, Tabelle je
 * Datensatz, Detailkarten mit Begründung und Schwellen, Profilbeschreibung.
 */
export function FlowauditRiskFlags(props: FlowauditRiskFlagsProps) {
  const { evaluation = null, locale } = props
  const { t, controller, state, selection } = useRiskFlags(props)
  const reference = evaluation?.profile ?? null
  const setFilter = (filter: RiskFilter): void => {
    controller.setFilter(filter)
    props.onFilterChange?.(controller.store.get().filter)
  }
  const selectRecord = (index: number): void => {
    const selected = controller.toggleRecord(index)
    props.onRecordSelect?.(selected)
  }
  const selectCode = (code: string): void => {
    controller.selectCode(code)
    props.onFilterChange?.(controller.store.get().filter)
  }
  return (
    <div className="fa-risk">
      <RiskHead heading={props.heading ?? ''} reference={reference} t={t} />
      <RiskFlagSummary rows={selection.rows} totals={selection.totals} dataset={selection.dataset} missingColumns={evaluation?.missing_columns ?? {}} locale={locale} onCodeSelect={selectCode} />
      <RiskFlagFilter filter={state.filter} onFilterChange={setFilter} rules={selection.rules} shown={selection.records.length} total={evaluation?.records.length ?? 0} locale={locale} />
      <div className="fa-risk__body">
        <RiskFlagTable
          columns={selection.tableColumns}
          rows={selection.tableRows}
          codes={selection.codes}
          selected={state.selectedIndex}
          locale={locale}
          onRecordSelect={selectRecord}
        />
        <RiskRecordDetail record={selection.selected} entries={selection.entries} profile={reference} locale={locale} />
      </div>
      <ProfileSection error={state.profileError} profile={state.profile} t={t} locale={locale} />
    </div>
  )
}
