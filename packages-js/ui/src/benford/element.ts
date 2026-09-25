import type { ElementDefinition } from '../elements/define'
import BenfordPanel from './BenfordPanel.vue'

/**
 * `<flowaudit-benford>`: Eigenschaften `port` (BenfordPort), `values`,
 * `locale`; Ereignisse `analysis-completed`, `error`.
 */
export const benfordElement: ElementDefinition = { tag: 'flowaudit-benford', component: BenfordPanel }
