export { default as ExtrapolationPanel } from './ExtrapolationPanel.vue'
export { extrapolationElement } from './element'
export { useExtrapolation, type ExtrapolationCallbacks, type UseExtrapolation } from './useExtrapolation'
/** Kern (Vertrag, Formularlogik, Zustandsautomat, Anzeige) aus `@flowaudit/ui-core`. */
export {
  extrapolationMessages,
  createExtrapolationRestPort,
  createExtrapolationController,
  extrapolationMethod,
  INITIAL_EXTRAPOLATION,
  buildEvaluationRequest,
  buildResidualRequest,
  conclusionLabel,
  conclusionTone,
  terMetrics,
  residualMetrics,
  type ExtrapolationController,
  type ExtrapolationData,
  type ExtrapolationPort,
  type ExtrapolationCatalogue,
  type EvaluationRequest,
  type EvaluationResult,
  type ResidualRequest,
  type ResidualResult,
  type StratumInput,
  type UnitInput,
} from '@flowaudit/ui-core'
