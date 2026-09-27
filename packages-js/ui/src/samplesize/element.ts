import type { ElementDefinition } from '../elements/define'
import SampleSizePlanner from './SampleSizePlanner.vue'

/** `<flowaudit-sample-size-planner>`: Eigenschaften `port`, `request`, `locale`; Ereignisse `plan-calculated`, `error`. */
export const sampleSizePlannerElement: ElementDefinition = { tag: 'flowaudit-sample-size-planner', component: SampleSizePlanner }
