import type { ElementDefinition } from '../elements/define'
import FaExtraction from './FaExtraction.vue'

/**
 * `<flowaudit-extraction>`: Eigenschaften `port` (ExtractionPort), `result`,
 * `locale`; Ereignisse `extraction-completed`, `error`.
 */
export const extractionElement: ElementDefinition = { tag: 'flowaudit-extraction', component: FaExtraction }
