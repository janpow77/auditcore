import type { ElementDefinition } from '../elements/define'
import BatchChecks from './BatchChecks.vue'

/** `<flowaudit-batch-checks>`: Eigenschaften `port`, `result`, `locale`; Ereignisse `checks-completed`, `error`. */
export const batchChecksElement: ElementDefinition = { tag: 'flowaudit-batch-checks', component: BatchChecks }
