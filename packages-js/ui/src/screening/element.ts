import type { ElementDefinition } from '../elements/define'
import ScreeningReview from './ScreeningReview.vue'

/**
 * `<flowaudit-screening-review>`: Eigenschaften `port` (ScreeningPort),
 * `runId`, `locale`; Ereignisse `run-created`, `decided`, `error`.
 */
export const screeningReviewElement: ElementDefinition = { tag: 'flowaudit-screening-review', component: ScreeningReview }
