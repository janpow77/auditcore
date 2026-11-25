import type { ElementDefinition } from '../elements/define'
import PdfRedaction from './PdfRedaction.vue'

/**
 * `<flowaudit-pdf-redaction>`: Eigenschaften `port` (RedactionPort), `locale`,
 * `urls`; Ereignisse `redaction-planned`, `redaction-completed`, `error`.
 */
export const pdfRedactionElement: ElementDefinition = { tag: 'flowaudit-pdf-redaction', component: PdfRedaction }
