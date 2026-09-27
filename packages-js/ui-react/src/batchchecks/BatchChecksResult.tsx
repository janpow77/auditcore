import { Fragment } from 'react'
import { saveFile } from '@auditcore/common/browser'
import {
  batchchecksFilterOptions,
  batchchecksFindingRows,
  batchchecksLevelText,
  batchchecksLevelTone,
  batchchecksMetricRows,
  batchchecksRuleRows,
  batchchecksSummaryText,
  type BatchchecksAnswer,
  type BatchchecksExportFormat,
} from '@auditcore/ui-core'
import { Badge } from '../base/Badge'
import { Button } from '../base/Button'
import type { UseBatchChecks } from './useBatchChecks'

/** Regelübersicht (wie die Regeltabelle in `BatchChecksResult.vue`). */
function Rules({ view, answer }: { view: UseBatchChecks; answer: BatchchecksAnswer }) {
  const { t } = view
  return (
    <div className="fa-batchchecks__scroll">
      <table className="fa-batchchecks__table" data-testid="batchchecks-rules">
        <thead>
          <tr>
            <th scope="col">{t('colCode')}</th>
            <th scope="col">{t('colTitle')}</th>
            <th scope="col">{t('colChecks')}</th>
            <th scope="col">{t('colStatus')}</th>
          </tr>
        </thead>
        <tbody>
          {batchchecksRuleRows(answer, t).map((rule) => (
            <tr key={rule.code} data-rule={rule.code}>
              <th scope="row">{rule.code}</th>
              <td>{rule.title}{rule.supplement ? <span className="fa-batchchecks__note">{t('supplement')}</span> : null}</td>
              <td>{rule.checks}{rule.basis ? <span className="fa-batchchecks__note">{rule.basis}</span> : null}</td>
              <td><Badge tone={rule.tone}>{rule.status}</Badge>{rule.note ? <span className="fa-batchchecks__note">{rule.note}</span> : null}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

/** Befunde mit Regelfilter (wie `BatchChecksFindings.vue`). */
function Findings({ view, answer }: { view: UseBatchChecks; answer: BatchchecksAnswer }) {
  const { t, controller, state } = view
  if (!answer.findings.length) return <><h4 className="fa-batchchecks__subheading">{t('findings')}</h4><p className="fa-batchchecks__muted">{t('findingsNone')}</p></>
  return (
    <>
      <h4 className="fa-batchchecks__subheading">{t('findings')}</h4>
      <label className="fa-batchchecks__field">
        <span className="fa-batchchecks__label">{t('filterRule')}</span>
        <select className="fa-batchchecks__input" value={state.ruleFilter ?? ''} data-testid="batchchecks-filter" onChange={(event) => controller.setRuleFilter(event.target.value || null)}>
          <option value="">{t('allRules')}</option>
          {batchchecksFilterOptions(answer).map((option) => <option key={option.code} value={option.code}>{option.label}</option>)}
        </select>
      </label>
      <div className="fa-batchchecks__scroll">
        <table className="fa-batchchecks__table" data-testid="batchchecks-findings">
          <thead>
            <tr>
              <th scope="col">{t('colId')}</th>
              <th scope="col">{t('colCode')}</th>
              <th scope="col">{t('colLevel')}</th>
              <th scope="col">{t('colMessage')}</th>
              <th scope="col">{t('colAffected')}</th>
              <th scope="col">{t('colBasis')}</th>
            </tr>
          </thead>
          <tbody>
            {batchchecksFindingRows(answer, state.ruleFilter, t).map((row) => (
              <tr key={row.id} data-finding={row.id} data-rule={row.rule}>
                <th scope="row">{row.id}</th>
                <td>{row.rule}</td>
                <td><Badge tone={row.tone}>{row.level}</Badge></td>
                <td>{row.message}</td>
                <td>{row.affected}</td>
                <td>{row.basis}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  )
}

/** Ergebnis: Eskalation, Kennzahlen, Export, Regeln und Befunde (wie `BatchChecksResult.vue`). */
export function BatchChecksResult({ view, answer, id }: { view: UseBatchChecks; answer: BatchchecksAnswer; id: string }) {
  const { t, locale, state, controller } = view
  const level = answer.summary.escalation_level
  const download = async (format: BatchchecksExportFormat): Promise<void> => {
    const file = await controller.exportRun(format)
    if (file && typeof URL.createObjectURL === 'function') saveFile(file)
  }
  return (
    <section className="fa-batchchecks__card" aria-labelledby={`${id}-result`} aria-live="polite" data-testid="batchchecks-result">
      <h3 id={`${id}-result`} className="fa-batchchecks__heading">{`${t('result')} `}<Badge tone={batchchecksLevelTone(level)} testId="batchchecks-level">{batchchecksLevelText(level, t)}</Badge></h3>
      <p className="fa-batchchecks__notice">{t('notice')}</p>
      <p data-testid="batchchecks-summary">{batchchecksSummaryText(answer, t)}</p>
      {answer.summary.report_blocked ? <p className="fa-batchchecks__failure" role="alert">{t('blocked', { reason: answer.summary.block_reason ?? '' })}</p> : null}
      <h4 className="fa-batchchecks__subheading">{t('metrics')}</h4>
      <dl className="fa-batchchecks__summary" data-testid="batchchecks-metrics">
        {batchchecksMetricRows(answer, t, locale).map((row) => (
          <Fragment key={row.label}>
            <dt>{row.label}</dt>
            <dd>{row.value}</dd>
          </Fragment>
        ))}
      </dl>
      {state.request ? (
        <div className="fa-batchchecks__actions">
          <Button loading={state.busy === 'export'} testId="batchchecks-export-json" onClick={() => void download('json')}>{t('exportJson')}</Button>
          <Button loading={state.busy === 'export'} testId="batchchecks-export-csv" onClick={() => void download('csv')}>{t('exportCsv')}</Button>
        </div>
      ) : null}
      <h4 className="fa-batchchecks__subheading">{t('rules')}</h4>
      <Rules view={view} answer={answer} />
      <Findings view={view} answer={answer} />
    </section>
  )
}
