import { Fragment, type ReactNode } from 'react'
import { identifierFacts, identifierReasonText, identifierStatusText, identifierStatusTone, type IdentifierResult } from '@auditcore/ui-core'
import type { UseIdentifierCheck } from './useIdentifierCheck'

function Fact({ label, children }: { label: string; children: ReactNode }) {
  return (
    <>
      <dt>{label}</dt>
      <dd>{children}</dd>
    </>
  )
}

/** Ergebnis einer Einzelprüfung: Status, Begründung, Normalform, Einzelheiten (wie `IdentifierResultView.vue`). */
export function IdentifierResultView({ view, result }: { view: UseIdentifierCheck; result: IdentifierResult }) {
  const { state, t, profile } = view
  const facts = state.catalogue ? identifierFacts(state.catalogue, result, t) : []
  return (
    <div className="fa-ident__result" aria-live="polite" data-testid="ident-result">
      <p className="fa-ident__status">
        <span className={`fa-ident__badge fa-ident__badge--${identifierStatusTone(result.status)}`}>{identifierStatusText(result.status, t)}</span>
        <span>{result.kind_label}</span>
      </p>
      <dl className="fa-ident__facts">
        <Fact label={t('message')}>{identifierReasonText(result, profile?.title ?? result.profile, t)}</Fact>
        {result.reason_label ? <Fact label={t('reason')}>{result.reason_label}</Fact> : null}
        {result.normalized ? <Fact label={t('normalized')}><code>{result.normalized}</code></Fact> : null}
        {result.country ? <Fact label={t('countryFound')}>{result.country}</Fact> : null}
      </dl>
      {facts.length ? (
        <details className="fa-ident__details">
          <summary>{t('details')}</summary>
          <dl className="fa-ident__facts">
            {facts.map((fact) => (
              <Fragment key={fact.key}>
                <dt>{fact.label}</dt>
                <dd>{fact.value}</dd>
              </Fragment>
            ))}
          </dl>
        </details>
      ) : null}
    </div>
  )
}
