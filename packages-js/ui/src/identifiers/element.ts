import type { ElementDefinition } from '../elements/define'
import IdentifierCheck from './IdentifierCheck.vue'

/**
 * `<flowaudit-identifier-check>`: Eigenschaften `port` (IdentifiersPort),
 * `locale`; Ereignisse `identifier-checked`, `batch-checked`, `error`.
 */
export const identifierCheckElement: ElementDefinition = { tag: 'flowaudit-identifier-check', component: IdentifierCheck }
