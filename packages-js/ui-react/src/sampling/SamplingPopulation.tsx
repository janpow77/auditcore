import { itemsFromImport, populationText, type Locale, type PopulationItem, type SamplingTranslate } from '@auditcore/ui-core'
import { TableImport } from '../tabular/TableImport'
import { useElementId } from '../store'

export interface SamplingPopulationProps {
  items: readonly PopulationItem[]
  t: SamplingTranslate
  locale: Locale
  /** Sprache des Datei-Imports wie in Vue (Prop der Hauptkomponente). */
  importLocale?: Locale
  onImport: (items: PopulationItem[]) => void
}

/** Grundgesamtheit mit Zusammenfassung und Datei-Import (wie `SamplingPopulation.vue`). */
export function SamplingPopulation({ items, t, locale, importLocale, onImport }: SamplingPopulationProps) {
  const id = useElementId('fa-sampling-population')
  return (
    <section className="fa-sampling__card" aria-labelledby={`${id}-title`}>
      <h3 id={`${id}-title`} className="fa-sampling__heading">{t('population')}</h3>
      {items.length ? (
        <p className="fa-sampling__muted" data-testid="sampling-population">{populationText(items, t, locale)}</p>
      ) : (
        <p className="fa-sampling__muted">{t('populationEmpty')}</p>
      )}
      <TableImport mode="items" locale={importLocale} onImport={(columns) => onImport(itemsFromImport(columns))} />
    </section>
  )
}
