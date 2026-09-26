import { useElementId } from '../store'
import { identifierProfileLabel } from '@flowaudit/ui-core'
import { IdentifierBatch } from './IdentifierBatch'
import { IdentifierSingle } from './IdentifierSingle'
import { useIdentifierCheck, type IdentifierInputs, type UseIdentifierCheck } from './useIdentifierCheck'

export type FlowauditIdentifierCheckProps = IdentifierInputs

function ProfileChoice({ view }: { view: UseIdentifierCheck }) {
  const { state, controller, t, profile } = view
  const catalogue = state.catalogue
  if (!catalogue) return null
  return (
    <div className="fa-ident__head">
      <label className="fa-ident__field">
        <span className="fa-ident__label">{t('profile')}</span>
        <select value={state.profileId ?? ''} className="fa-ident__select" data-testid="ident-profile" onChange={(event) => controller.setProfile(event.target.value || null)}>
          <option value="">{t('choose')}</option>
          {catalogue.profiles.map((entry) => <option key={entry.id} value={entry.id}>{identifierProfileLabel(catalogue, entry, t)}</option>)}
        </select>
      </label>
      {profile ? (
        <details className="fa-ident__source">
          <summary>{t('profileSource')}</summary>
          <p>{profile.rationale}</p>
          <p>{profile.origin}</p>
        </details>
      ) : null}
    </div>
  )
}

/**
 * „Kennung prüfen“ als native React-Komponente (Vertrag wie
 * `<flowaudit-identifier-check>`): Prüfprofil, Einzelprüfung mit Begründung
 * und Stapelprüfung aus einer Tabelle. Ereignisse: `onIdentifierChecked`,
 * `onBatchChecked`, `onError`.
 */
export function FlowauditIdentifierCheck(props: FlowauditIdentifierCheckProps) {
  const view = useIdentifierCheck(props)
  const { state, t } = view
  const id = useElementId('fa-ident')
  return (
    <div className="fa-ident" lang={view.locale}>
      {props.port ? null : <p className="fa-ident__muted" role="status">{t('noPort')}</p>}
      {state.busy === 'load' ? <p className="fa-ident__muted" role="status">{t('loading')}</p> : null}
      {state.error ? <p className="fa-ident__failure" role="alert">{t('failed', { message: state.error })}</p> : null}
      {state.catalogue ? (
        <>
          <ProfileChoice view={view} />
          <div className="fa-ident__columns">
            <IdentifierSingle view={view} id={id} />
            <IdentifierBatch view={view} id={id} />
          </div>
        </>
      ) : null}
    </div>
  )
}
