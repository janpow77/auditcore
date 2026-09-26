import type { ElementDefinition } from '../elements/define'
import FaDsfa from './FaDsfa.vue'
import FaVvt from './FaVvt.vue'

/**
 * `<flowaudit-vvt>`: Eigenschaften `port` (DataProtectionPort), `actor`,
 * `editable`, `locale`; Ereignisse `draft-saved`, `released`, `exported`, `error`.
 */
export const vvtElement: ElementDefinition = { tag: 'flowaudit-vvt', component: FaVvt }

/**
 * `<flowaudit-dsfa>`: Eigenschaften `port`, `activityId`, `actor`, `editable`,
 * `locale`; Ereignisse `assessment-change`, `error`.
 */
export const dsfaElement: ElementDefinition = { tag: 'flowaudit-dsfa', component: FaDsfa }
