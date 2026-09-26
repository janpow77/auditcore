import type { ElementDefinition } from '../elements/define'
import FaComparisons from './FaComparisons.vue'

/**
 * `<flowaudit-comparisons>`: `port` als JS-Eigenschaft (z. B. `createSynopsisRestClient`);
 * Ereignisse `comparison-created`, `comparison-imported`, `comparison-removed`,
 * `comparison-open`, `error`.
 */
export const comparisonsElement: ElementDefinition = { tag: 'flowaudit-comparisons', component: FaComparisons }
