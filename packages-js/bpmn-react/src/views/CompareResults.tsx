/** Results of the comparison panel: target/actual check and version synopsis. */

import { changeLabel, synopsis, type Comparison, type TargetActualCheck } from '@flowaudit/bpmn-flowaudit'
import { FaIcon } from '../base/FaIcon'
import { useI18n } from '../i18n'

export function CheckResults({ check }: { check: TargetActualCheck }) {
  const { t } = useI18n()
  return (
    <>
      <p className="fa-badge fa-badge--info" role="status">{t('compare.summary', { met: check.met, notMet: check.notMet, extra: check.additionalInActual.length })}</p>
      <ul className="fa-compare__results">
        {check.results.map((result) => (
          <li key={result.targetId} className={result.met ? 'fa-compare__met' : 'fa-compare__not-met'}>
            <FaIcon name={result.met ? 'check' : 'close'} size={14} />
            <strong>{result.name}</strong>
            {result.reasons.map((reason) => <span key={reason} className="fa-help">{reason}</span>)}
          </li>
        ))}
      </ul>
    </>
  )
}

export function ComparisonTable({ comparison }: { comparison: Comparison }) {
  const { t } = useI18n()
  const rows = synopsis(comparison)
  return (
    <>
      {!rows.length ? (
        <p className="fa-help">{t('compare.unchanged')}</p>
      ) : (
        <table className="fa-table">
          <thead><tr><th>{t('compare.element')}</th><th>{t('compare.field')}</th><th>{t('compare.before')}</th><th>{t('compare.after')}</th><th>{t('compare.change')}</th></tr></thead>
          <tbody>
            {rows.map((row, position) => <tr key={position}><td>{row.element}</td><td>{row.field}</td><td>{row.before}</td><td>{row.after}</td><td>{row.change}</td></tr>)}
          </tbody>
        </table>
      )}
      <p className="fa-compare__legend">
        <span className="fa-badge fa-badge--success">{changeLabel('hinzugefuegt')}</span>
        <span className="fa-badge fa-badge--danger">{changeLabel('entfallen')}</span>
        <span className="fa-badge fa-badge--warning">{changeLabel('geaendert')}</span>
      </p>
    </>
  )
}
