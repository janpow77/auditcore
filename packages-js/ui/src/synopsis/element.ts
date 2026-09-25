import type { ElementDefinition } from '../elements/define'
import FaSynopsis from './FaSynopsis.vue'

/**
 * `<flowaudit-synopsis>`: `comparison`/`result` und `port` als JS-Eigenschaften;
 * Ereignisse `row-update`, `export`, `navigate`, `update:layout`.
 */
export const synopsisElement: ElementDefinition = { tag: 'flowaudit-synopsis', component: FaSynopsis }
