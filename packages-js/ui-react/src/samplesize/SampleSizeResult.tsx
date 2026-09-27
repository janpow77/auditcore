import { samplesizeAllocation, samplesizeDerivation, samplesizeSummary, type Locale, type SampleSizePlan, type SamplesizeMessageKey, type Translate } from '@auditcore/ui-core'

function Table({ testId, caption, head, rows }: { testId: string; caption: string; head: string[]; rows: string[][] }) {
  return (
    <table className="fa-samplesize__table" data-testid={testId}>
      <caption>{caption}</caption>
      <thead><tr>{head.map((cell) => <th key={cell} scope="col">{cell}</th>)}</tr></thead>
      <tbody>{rows.map((row, index) => <tr key={index}>{row.map((cell, column) => <td key={column}>{cell}</td>)}</tr>)}</tbody>
    </table>
  )
}

/** Ergebnis des Planers (wie `SampleSizeResult.vue`). */
export function SampleSizeResult({ plan, t, locale }: { plan: SampleSizePlan; t: Translate<SamplesizeMessageKey>; locale: Locale }) {
  const allocation = samplesizeAllocation(plan, t, locale)
  return (
    <section className="fa-samplesize__result" aria-label={t('result')} data-testid="samplesize-result">
      <h3 className="fa-samplesize__heading">{t('result')} <span className="fa-samplesize__badge">{plan.status_label}</span></h3>
      <dl className="fa-samplesize__summary">
        {samplesizeSummary(plan, t, locale).map((row) => (
          <div key={row.key}>
            <dt>{row.key}</dt>
            <dd>{row.text}</dd>
          </div>
        ))}
      </dl>
      {allocation.length ? <Table testId="samplesize-allocation" caption={t('allocation')} head={[t('stratumName'), t('allocationSize'), t('allocationShare'), t('allocationCutOff'), t('stratumExhaustive')]} rows={allocation} /> : null}
      <Table testId="samplesize-derivation" caption={t('derivation')} head={[t('stepLabel'), t('stepFormula'), t('stepValue'), t('stepSource')]} rows={samplesizeDerivation(plan, locale)} />
      {plan.warnings.length ? (
        <ul className="fa-samplesize__warnings" aria-label={t('warnings')}>
          {plan.warnings.map((warning) => <li key={warning}>{warning}</li>)}
        </ul>
      ) : null}
    </section>
  )
}
