export { default as PdfRedaction } from './PdfRedaction.vue'
export { pdfRedactionElement } from './element'
/** Kern (Texte, Port, Zustandsautomat, Anzeige) aus `@auditcore/ui-core`. */
export {
  redactionMessages,
  createRedactionController,
  createRedactionRestPort,
  INITIAL_REDACTION,
  type RedactionCatalogue,
  type RedactionController,
  type RedactionData,
  type RedactionPlan,
  type RedactionPort,
  type RedactionResult,
  type RedactionSelection,
  type RedactionUrls,
} from '@auditcore/ui-core'
