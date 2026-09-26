import {
  conclusionLabel,
  conclusionTone,
  extrapolationStepColumns,
  extrapolationStepRows,
  terMetrics,
  type EvaluationResult,
  type ExtrapolationCatalogue,
  type ExtrapolationExportFormat,
  type ExtrapolationMetric,
  type ExtrapolationTranslate,
  type Locale,
} from '@auditcore/ui-core'
import { Badge } from '../base/Badge'
import { Button } from '../base/Button'
import { useElementId } from '../store'
import { FlowauditTable } from '../table/FlowauditTable'

export interface ExtrapolationResultProps {
  result: EvaluationResult
  catalogue: ExtrapolationCatalogue | null
  busy: boolean
  t: ExtrapolationTranslate
  locale: Locale
  /** Sprache der Tabelle wie in Vue (Prop der Hauptkomponente). */
  tableLocale?: Locale
  onExport: (format: ExtrapolationExportFormat) => void
}

/** Kennzahlen als Beschreibungsliste (gemeinsam für TER und RER). */
export function MetricList({ metrics, testId }: { metrics: readonly ExtrapolationMetric[]; testId: string }) {
  return (
    <dl className="fa-extrapolation__metrics" data-testid={testId}>
      {metrics.map((metric) => (
        <div key={metric.id} className="fa-extrapolation__metric" data-metric={metric.id}>
          <dt>{metric.label}</dt>
          <dd className="fa-extrapolation__value">{metric.value}</dd>
          {metric.detail ? <dd className="fa-extrapolation__muted">{metric.detail}</dd> : null}
        </div>
      ))}
    </dl>
  )
}

/** Gesamtfehlerquote mit Ergebnis, Kennzahlen, Erläuterung, Herleitung und Export (wie `ExtrapolationResult.vue`). */
export function ExtrapolationResult({ result, catalogue, busy, t, locale, tableLocale, onExport }: ExtrapolationResultProps) {
  const id = useElementId('fa-extrapolation-result')
  const ter = result.total_error_rate
  const warnings = result.projection.warnings
  return (
    <section className="fa-extrapolation__card fa-extrapolation__card--result" aria-labelledby={`${id}-title`} aria-live="polite">
      <h3 id={`${id}-title`} className="fa-extrapolation__heading">{t('resultTitle')}</h3>
      <p className="fa-extrapolation__conclusion">
        <Badge tone={conclusionTone(ter.conclusion)} testId="extrapolation-conclusion">{conclusionLabel(catalogue, ter.conclusion)}</Badge>
        <span className="fa-extrapolation__muted">{result.method.label}</span>
      </p>
      <p className="fa-extrapolation__hint">{t('resultNotice')}</p>
      <MetricList metrics={terMetrics(result, t, locale)} testId="extrapolation-metrics" />
      <h4 className="fa-extrapolation__heading">{t('explanation')}</h4>
      <ul className="fa-extrapolation__list">
        {ter.explanation.map((line) => <li key={line}>{line}</li>)}
      </ul>
      {warnings.length ? (
        <>
          <h4 className="fa-extrapolation__heading">{t('warnings')}</h4>
          <ul className="fa-extrapolation__warnings">
            {warnings.map((line) => <li key={line}>{line}</li>)}
          </ul>
        </>
      ) : null}
      <details className="fa-extrapolation__derivation">
        <summary>{t('derivation')}</summary>
        <FlowauditTable columns={extrapolationStepColumns(t, locale)} rows={extrapolationStepRows(result)} caption={t('derivation')} locale={tableLocale} testId="extrapolation-steps" />
      </details>
      <p className="fa-extrapolation__fingerprint">{`${t('fingerprint')}: ${result.fingerprint}`}</p>
      <div className="fa-extrapolation__actions">
        <Button loading={busy} testId="extrapolation-export-csv" onClick={() => onExport('csv')}>{t('exportCsv')}</Button>
        <Button disabled={busy} testId="extrapolation-export-json" onClick={() => onExport('json')}>{t('exportJson')}</Button>
      </div>
    </section>
  )
}
