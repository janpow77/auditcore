import type { ElementDefinition } from '../elements/define'
import RiskFlags from './RiskFlags.vue'

/**
 * `<flowaudit-risk-flags>`: Eigenschaften `evaluation` (Antwort von `POST /evaluate`)
 * und `profile` (Antwort von `GET /profiles/{id}/{version}`) als JS-Objekte;
 * Ereignisse `record-select` und `filter-change`.
 */
export const riskFlagsElement: ElementDefinition = { tag: 'flowaudit-risk-flags', component: RiskFlags }
