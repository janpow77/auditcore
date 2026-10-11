import type { ElementDefinition } from '../elements/define'
import FaDatenschutzAssistent from './FaDatenschutzAssistent.vue'
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

/**
 * `<flowaudit-datenschutz-assistent>`: Eigenschaften `port` (AssistantPort),
 * `activityId`, `locale`; Ereignisse `change`, `error`. Der Assistent ist
 * optional: geführt Schritt für Schritt oder frei.
 */
export const assistantElement: ElementDefinition = { tag: 'flowaudit-datenschutz-assistent', component: FaDatenschutzAssistent }
