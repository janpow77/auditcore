export { default as FaComparisons } from './FaComparisons.vue'
export { default as ComparisonForm } from './ComparisonForm.vue'
export { default as ComparisonList } from './ComparisonList.vue'
export { comparisonsElement } from './element'
export { useComparisons, type ComparisonsSource, type UseComparisons } from './useComparisons'
/** Kern (Formular, Liste, Import, Zustandsautomat) aus `@flowaudit/ui-core`. */
export {
  comparisonsMessages,
  type ComparisonsMessageKey,
  type ComparisonsTranslate,
  COMPARISON_KINDS,
  COMPARISON_MODES,
  ACCEPTED_EXTENSIONS,
  DEFAULT_MAX_UPLOAD_BYTES,
  DEFAULT_FORM,
  formProblems,
  toCompareFields,
  parseImport,
  summaryView,
  filterSummaries,
  comparisonsView,
  createComparisonsController,
  synopsisPortOf,
  type CompareForm,
  type ComparisonKind,
  type ComparisonMode,
  type ComparisonsPort,
  type ComparisonsError,
  type ComparisonsData,
  type ComparisonsView,
  type ComparisonsController,
  type ImportRequest,
  type SummaryView,
} from '@flowaudit/ui-core'
