import type { ElementDefinition } from '../elements/define'
import AttributeSampling from './AttributeSampling.vue'

/** `<flowaudit-attribute-sampling>`: Eigenschaften `port`, `locale`; Ereignisse `evaluation-completed`, `error`. */
export const attributeSamplingElement: ElementDefinition = { tag: 'flowaudit-attribute-sampling', component: AttributeSampling }
