import { derivationColumns, derivationRows, sizeTexts, type Locale, type SamplingTranslate, type SizeResult } from '@flowaudit/ui-core'
import { FlowauditTable } from '../table/FlowauditTable'
import { useElementId } from '../store'

export interface SamplingResultProps {
  result: SizeResult
  t: SamplingTranslate
  locale: Locale
  /** Sprache der Tabelle wie in Vue (Prop der Hauptkomponente). */
  tableLocale?: Locale
}

/** Stichprobenumfang mit Intervall, Warnungen und Herleitung (wie `SamplingResult.vue`). */
export function SamplingResult({ result, t, locale, tableLocale }: SamplingResultProps) {
  const id = useElementId('fa-sampling-result')
  const texts = sizeTexts(result, t, locale)
  const rows = derivationRows(result)
  return (
    <section className="fa-sampling__card fa-sampling__card--result" aria-labelledby={`${id}-title`} aria-live="polite">
      <h3 id={`${id}-title`} className="fa-sampling__heading">{t('result')}</h3>
      <p className="fa-sampling__size" data-testid="sampling-size">{texts.size}</p>
      {result.kind === 'mus' ? <p className="fa-sampling__muted">{texts.interval}</p> : null}
      {result.warnings.length ? (
        <ul className="fa-sampling__warnings">
          {result.warnings.map((warning) => <li key={warning}>{warning}</li>)}
        </ul>
      ) : null}
      {rows.length ? <FlowauditTable columns={derivationColumns(t, locale)} rows={rows} caption={t('derivation')} locale={tableLocale} /> : null}
    </section>
  )
}
