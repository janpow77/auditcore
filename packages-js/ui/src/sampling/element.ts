import type { ElementDefinition } from '../elements/define'
import SamplingPanel from './SamplingPanel.vue'

/**
 * `<flowaudit-sampling>`: Eigenschaften `port` (SamplingPort), `items`
 * (Grundgesamtheit), `locale`; Ereignisse `size-calculated`,
 * `selection-drawn`, `error`.
 */
export const samplingElement: ElementDefinition = { tag: 'flowaudit-sampling', component: SamplingPanel }
