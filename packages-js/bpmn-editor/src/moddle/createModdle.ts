import { BpmnModdle } from 'bpmn-moddle'

import type { Moddle } from '../types'

export const BIOC_NAMESPACE = 'http://bpmn.io/schema/bpmn/biocolor/1.0'
export const COLOR_NAMESPACE = 'http://www.omg.org/spec/BPMN/non-normative/color/1.0'

/**
 * Erzeugt eine moddle-Instanz mit BPMN 2.0 samt DI und den Farb-Namensräumen
 * `bioc` und `color` (beide bringt bpmn-moddle mit) sowie beliebigen
 * zusätzlichen Erweiterungen (z. B. `flowaudit`).
 */
export function createModdle(extensions: Record<string, unknown> = {}): Moddle {
  return new BpmnModdle(extensions)
}
