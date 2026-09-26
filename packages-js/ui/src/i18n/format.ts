/**
 * Formatierer seit 0.2.0 aus `@flowaudit/common` (framework-frei); Namen und
 * Verhalten unverändert. Für Berliner Zeit und den Ersatzwert „—“ direkt
 * `formatDate`/`formatNumber` aus `@flowaudit/common` verwenden.
 */
export {
  localeTag,
  intlFormatDate as formatDate,
  intlFormatNumber as formatNumber,
  intlFormatPercent as formatPercent,
} from '@flowaudit/common'
