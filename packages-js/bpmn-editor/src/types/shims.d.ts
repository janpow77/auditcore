declare module 'bpmn-moddle' {
  import type { Moddle } from './index'

  /** bpmn-moddle ohne mitgelieferte Typen: Konstruktor liefert eine moddle-Instanz. */
  export const BpmnModdle: new (packages?: Record<string, unknown>, options?: Record<string, unknown>) => Moddle
}
