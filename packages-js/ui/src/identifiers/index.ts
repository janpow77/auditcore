export { default as IdentifierCheck } from './IdentifierCheck.vue'
export { identifierCheckElement } from './element'
export { useIdentifierCheck, type IdentifierCallbacks, type UseIdentifierCheck } from './useIdentifierCheck'
/** Kern (Vertrag, Zustandsautomat, Anzeige) aus `@auditcore/ui-core`. */
export {
  identifierMessages,
  createIdentifiersRestPort,
  createIdentifierController,
  type IdentifierController,
  type IdentifierData,
  type IdentifiersPort,
  type IdentifierCatalogue,
  type IdentifierResult,
  type IdentifierBatchAnswer,
} from '@auditcore/ui-core'
