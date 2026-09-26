import { downloadText, identifierBatchCsv, identifierBatchLines, identifierBatchSummary } from '@auditcore/ui-core'
import { Button } from '../base/Button'
import type { UseIdentifierCheck } from './useIdentifierCheck'

/** Ergebnis der Stapelprüfung: Zusammenfassung, Filter, CSV-Export und Tabelle (wie `IdentifierBatchResult.vue`). */
export function IdentifierBatchResult({ view }: { view: UseIdentifierCheck }) {
  const { state, controller, t } = view
  const { catalogue, batch: answer } = state
  if (!catalogue || !answer) return null
  const lines = identifierBatchLines(catalogue, answer, state.batchRequest, state.onlyIssues, t)
  const exportCsv = (): void => {
    downloadText(identifierBatchCsv(catalogue, answer, state.batchRequest, t), 'kennungspruefung.csv', 'text/csv;charset=utf-8')
  }
  const columns = ['colRef', 'colKind', 'colValue', 'colStatus', 'colReason', 'colNormalized'] as const
  return (
    <div className="fa-ident__batch" aria-live="polite" data-testid="ident-batch-result">
      <p className="fa-ident__summary">{identifierBatchSummary(answer, t)}</p>
      <div className="fa-ident__actions">
        <label className="fa-ident__check">
          <input type="checkbox" checked={state.onlyIssues} data-testid="ident-only-issues" onChange={(event) => controller.setField('onlyIssues', event.target.checked)} />
          {t('onlyInvalid')}
        </label>
        <Button testId="ident-export" onClick={exportCsv}>{t('export')}</Button>
      </div>
      <div className="fa-ident__scroll">
        <table className="fa-ident__table">
          <thead>
            <tr>{columns.map((key) => <th key={key} scope="col">{t(key)}</th>)}</tr>
          </thead>
          <tbody>
            {lines.map((line) => (
              <tr key={line.key}>
                <td>{line.ref}</td>
                <td>{line.kind}</td>
                <td><code>{line.value}</code></td>
                <td><span className={`fa-ident__badge fa-ident__badge--${line.tone}`}>{line.status}</span></td>
                <td>{line.reason}</td>
                <td><code>{line.normalized}</code></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
