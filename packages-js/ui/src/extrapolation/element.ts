import type { ElementDefinition } from '../elements/define'
import ExtrapolationPanel from './ExtrapolationPanel.vue'

/**
 * `<flowaudit-extrapolation>`: Eigenschaften `port` (ExtrapolationPort),
 * `strata`, `units`, `locale`; Ereignisse `evaluation-completed`,
 * `residual-computed`, `error`.
 */
export const extrapolationElement: ElementDefinition = { tag: 'flowaudit-extrapolation', component: ExtrapolationPanel }
