import type { ElementDefinition } from '../elements/define'
import BatchChecks from './BatchChecks.vue'

/** `<flowaudit-batch-checks>`: Eigenschaften `port`, `locale`; Ereignisse `item-select`, `error`. */
export const batchChecksElement: ElementDefinition = { tag: 'flowaudit-batch-checks', component: BatchChecks }
