/**
 * Formatierer seit 0.2.0 aus `@auditcore/common` (framework-frei); Namen und
 * Verhalten unverändert. Für Berliner Zeit und den Ersatzwert „—“ direkt
 * `formatDate`/`formatNumber` aus `@auditcore/common` verwenden.
 */
export {
  localeTag,
  intlFormatDate as formatDate,
  intlFormatNumber as formatNumber,
  intlFormatPercent as formatPercent,
} from '@auditcore/common'
