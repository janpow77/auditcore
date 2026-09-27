import type { RunnerItem, RunnerPort } from './types'

/**
 * Port im Arbeitsspeicher (Demo, Tests). Eine REST-Umsetzung baut auf
 * `requestJson` aus `@auditcore/common` auf (Vorbild: `extrapolation/rest-port.ts`).
 */
export function createRunnerMemoryPort(items: readonly RunnerItem[]): RunnerPort {
  return { list: async () => items }
}
