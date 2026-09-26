import {
  excludedLines,
  selectionColumns,
  selectionRows,
  selectionTexts,
  strataColumns,
  strataRows,
  type ExportFormat,
  type Locale,
  type SamplingTranslate,
  type SelectionResult,
} from '@auditcore/ui-core'
import { Badge } from '../base/Badge'
import { Button } from '../base/Button'
import { FlowauditTable } from '../table/FlowauditTable'

export interface SamplingSelectionResultProps {
  result: SelectionResult
  busy?: boolean
  t: SamplingTranslate
  locale: Locale
  /** Sprache der Tabellen wie in Vue (Prop der Hauptkomponente). */
  tableLocale?: Locale
  onExport: (format: ExportFormat) => void
}

/** Gezogene Stichprobe mit Seed, Allokation, Auswahl und Export (wie `SamplingSelectionResult.vue`). */
export function SamplingSelectionResult({ result, busy = false, t, locale, tableLocale, onExport }: SamplingSelectionResultProps) {
  const texts = selectionTexts(result, t, locale)
  const excluded = excludedLines(result, t)
  return (
    <div className="fa-sampling__selection" aria-live="polite">
      <p className="fa-sampling__seed" data-testid="sampling-seed-used">
        <Badge tone="accent">{texts.seed}</Badge>
        <span className="fa-sampling__muted">{texts.origin}</span>
        <span>{texts.summary}</span>
      </p>
      <p className="fa-sampling__hint">{texts.reproducible}</p>
      <FlowauditTable columns={strataColumns(result, t, locale)} rows={strataRows(result)} caption={t('allocationTable')} locale={tableLocale} testId="sampling-strata" />
      {excluded.length ? (
        <ul className="fa-sampling__warnings">
          {excluded.map((line) => <li key={line}>{line}</li>)}
        </ul>
      ) : null}
      <FlowauditTable columns={selectionColumns(result, t, locale)} rows={selectionRows(result)} rowKey="order" caption={t('selection')} locale={tableLocale} testId="sampling-rows" />
      <div className="fa-sampling__actions">
        <Button loading={busy} testId="sampling-export-csv" onClick={() => onExport('csv')}>{t('exportCsv')}</Button>
        <Button disabled={busy} testId="sampling-export-json" onClick={() => onExport('json')}>{t('exportJson')}</Button>
      </div>
    </div>
  )
}
